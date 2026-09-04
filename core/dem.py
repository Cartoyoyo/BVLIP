# -*- coding: utf-8 -*-
"""Telechargement du MNT RGE ALTI sur une emprise, en GeoTIFF Lambert 93.

Le service WMS renvoie les altitudes en BIL 32 bits, seul format qui porte de
vraies valeurs flottantes. La limite de 5010 pixels par requete impose de
decouper les grandes emprises en dalles, reassemblees ici en un seul raster.

L'emprise est calee sur la grille de la resolution demandee, pour que deux
appels voisins produisent des pixels alignes.
"""

import math
import os
import struct

import numpy as np
from osgeo import gdal, osr

from .geoservices import (
    LAYER_DEM, WMS_MAX_PIXELS, GeoserviceError, wms_bil,
)

DEFAULT_RESOLUTION = 5.0  # RGE ALTI 5 m
NODATA = -99999.0

# Bornes de plausibilite des altitudes, et detection des pics aberrants.
#
# Le service ne rend pas que du relief. Verifie sur un carre d'un kilometre
# du bassin de l'Allier, ou le terrain est un versant banal :
#
#     maille  5 m -> altitudes de 371,4 a 535,9 m, rien de negatif
#     maille 25 m -> altitudes de 371,8 a 535,1 m, rien de negatif
#     maille 50 m -> altitudes de -97,4 a 534,2 m
#
# Les valeurs fausses n'existent donc dans aucune donnee source : elles
# apparaissent au rééchantillonnage du service vers les mailles grossieres,
# sans doute par melange avec des mailles sans donnee. On ne les voyait pas
# jusqu'ici parce qu'un petit bassin se calcule a 5 m ; elles surgissent des
# qu'une grande emprise impose une maille large.
#
# Non filtrees, elles passent pour du relief et ruinent tout ce qui en
# depend : sur l'Allier a Vichy, une denivelee de 6535 m au lieu de 1936, et
# un ecoulement qui se jette dans un puits qui n'existe pas.
#
# Deux criteres, parce qu'aucun ne suffit seul. Le premier est absolu et
# vaut partout : le point le plus bas de France metropolitaine est a environ
# -2 m, rien en dessous de -10 m n'est du terrain. Le second est relatif et
# rattrape le reste : une maille qui plonge de plus de 300 m sous *toutes*
# celles d'un anneau a trois mailles n'est pas un relief mais un trou, aucun
# versant francais ne descendant si vite.
Z_MIN_PLAUSIBLE = -10.0
Z_MAX_PLAUSIBLE = 5000.0

# Rayon de l'anneau de comparaison, en mailles, et chute minimale sous sa
# mediane pour declarer un artefact. Mesure sur l'Allier a Vichy : a ce
# reglage, cinquante-sept mailles sont reprises et l'altitude minimale du
# bassin passe de 111,7 m - impossible, la ville est a 250 - a 250,1 m.
SPIKE_RING_CELLS = 3
SPIKE_DROP = 200.0

# Memoire que la recherche d'anneau s'autorise par bande. Cent-vingt-huit
# megaoctets tiennent partout et laissent des bandes de plusieurs centaines
# de lignes, donc peu de tours.
RING_CHUNK_BYTES = 128e6

# Distance de recherche, en mailles, pour combler une maille ecartee.
FILL_SEARCH_CELLS = 10
LAMBERT93_EPSG = 2154

# Le service annonce du BIL 32 bits sans preciser l'ordre des octets ; il est
# en petit-boutien. On garde la constante explicite pour que la lecture reste
# lisible et modifiable si le service evoluait.
BIL_DTYPE = "<f4"


class DemError(RuntimeError):
    """Le MNT n'a pas pu etre constitue sur l'emprise demandee."""


# Resolutions proposees a l'ajustement automatique, de la plus fine a la plus
# grossiere. Le RGE ALTI est natif au metre et au 5 metres ; au-dela, le
# service reechantillonne, ce qui reste pertinent : sur un bassin de plusieurs
# centaines de kilometres carres, une maille de 25 m ne deplace ni la ligne de
# partage des eaux ni les caracteristiques qu'on en tire.
RESOLUTION_STEPS = (5.0, 10.0, 25.0, 50.0)

# Memoire consommee par maille sur l'ensemble de la chaine : le MNT, les
# rasters d'ecoulement produits par GRASS, et les tableaux du calcul des
# caracteristiques avec leurs intermediaires. Mesure empirique, prise large.
BYTES_PER_PIXEL = 40

# Part de la memoire libre que le traitement s'autorise. Le reste doit suffire
# a QGIS, a GRASS lance en sous-processus et au systeme.
MEMORY_SHARE = 0.35

# Bornes du plafond, quand la memoire libre n'est pas mesurable ou qu'elle
# donne une valeur aberrante.
MIN_PIXELS = 2e6
MAX_PIXELS = 60e6
FALLBACK_PIXELS = 12e6


def available_memory():
    """Memoire vive disponible en octets, ou None si elle n'est pas lisible."""
    try:  # Windows
        import ctypes

        class _Status(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = _Status()
        status.dwLength = ctypes.sizeof(_Status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return int(status.ullAvailPhys)
    except (AttributeError, OSError, ImportError):
        pass
    try:  # Linux
        with open("/proc/meminfo", encoding="ascii") as handle:
            for line in handle:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) * 1024
    except OSError:
        pass
    return None


def max_pixels_for_memory():
    """Nombre de mailles que la memoire libre permet de traiter.

    Le plafond ne peut pas etre une constante : la meme emprise passe sans
    difficulte sur un poste a 32 Go et fait tomber QGIS sur un poste a 8 Go
    dont il ne reste que deux libres. On le deduit donc de ce qui est
    reellement disponible au moment du calcul.
    """
    free = available_memory()
    if not free:
        return FALLBACK_PIXELS
    budget = free * MEMORY_SHARE / BYTES_PER_PIXEL
    return max(MIN_PIXELS, min(MAX_PIXELS, budget))


def pixel_count(bbox, resolution):
    xmin, ymin, xmax, ymax = bbox
    return ((xmax - xmin) / resolution) * ((ymax - ymin) / resolution)


def choose_resolution(bbox, max_pixels=None, steps=RESOLUTION_STEPS):
    """Retient la maille la plus fine qui tienne sous le plafond de mailles.

    Sans cet ajustement, un grand bassin demande un MNT que la machine ne peut
    pas traiter : le telechargement passe encore, mais la suite reclame
    plusieurs gigaoctets et QGIS s'arrete net, sans message ni trace. Mieux
    vaut une maille plus large qu'un plantage.

    Renvoie (resolution, nombre de mailles, plafond retenu). Si meme la plus
    grossiere ne suffit pas, elle est renvoyee quand meme : c'est a l'appelant
    de decider s'il refuse.
    """
    if max_pixels is None:
        max_pixels = max_pixels_for_memory()
    for resolution in steps:
        count = pixel_count(bbox, resolution)
        if count <= max_pixels:
            return resolution, count, max_pixels
    return steps[-1], pixel_count(bbox, steps[-1]), max_pixels


def snap_bbox(bbox, resolution):
    """Cale l'emprise sur la grille de la resolution, en l'arrondissant vers
    l'exterieur. Renvoie (bbox calee, largeur px, hauteur px)."""
    xmin, ymin, xmax, ymax = bbox
    xmin = math.floor(xmin / resolution) * resolution
    ymin = math.floor(ymin / resolution) * resolution
    xmax = math.ceil(xmax / resolution) * resolution
    ymax = math.ceil(ymax / resolution) * resolution
    width = int(round((xmax - xmin) / resolution))
    height = int(round((ymax - ymin) / resolution))
    if width < 1 or height < 1:
        raise DemError("Emprise trop petite pour la resolution demandee.")
    return (xmin, ymin, xmax, ymax), width, height


def _tiles(width, height, step):
    """Decoupe la grille en dalles au plus grandes que la limite du service."""
    for row in range(0, height, step):
        for col in range(0, width, step):
            yield col, row, min(step, width - col), min(step, height - row)


def _unpack(payload, width, height):
    """Convertit les octets BIL en liste de listes de flottants, ligne par
    ligne du nord vers le sud (ordre natif du format)."""
    values = struct.unpack("<{0}f".format(width * height), payload)
    return [values[r * width:(r + 1) * width] for r in range(height)]


def _ring_median(grid, radius):
    """Mediane des mailles situees a exactement radius mailles de distance.

    L'anneau, et non le carre plein : ce qu'on veut savoir, c'est a quelle
    altitude est le terrain *autour* de la maille, sans y meler ses voisines
    immediates, qui appartiennent souvent au meme artefact.

    La mediane, et non le minimum. Le minimum semblait plus prudent ; il est
    en fait aveugle des que l'artefact s'etend jusqu'a l'anneau. Observe sur
    l'Allier : une bande de quatre mailles fausses dont l'anneau contient
    encore un bout, minimum a 144,9 m contre 111,7 m au centre, soit une
    chute de 33 m - rien de suspect, alors que le terrain reel est a 600 m.
    La mediane de ce meme anneau vaut 600 m et denonce la maille aussitot.

    Elle discrimine aussi mieux le relief : sur un versant regulier, l'anneau
    est symetrique autour de la maille, sa mediane vaut donc a peu pres la
    maille elle-meme, et la pente la plus raide ne declenche rien.
    """
    height, width = grid.shape
    padded = np.pad(grid, radius, mode="edge")
    offsets = [
        (dy, dx)
        for dy in range(2 * radius + 1)
        for dx in range(2 * radius + 1)
        if max(abs(dy - radius), abs(dx - radius)) == radius
    ]

    # Le calcul se fait par bandes. Une mediane demande d'avoir les valeurs
    # de l'anneau ensemble, soit vingt-quatre copies du raster a trois
    # mailles de rayon : 1,7 Go sur un bassin de 1 860 km2 a 10 m, et le
    # calcul tombait faute de memoire. Par bandes, l'empreinte ne depend plus
    # de la hauteur du raster.
    rows = max(1, int(RING_CHUNK_BYTES / (len(offsets) * width * 4)))
    result = np.empty_like(grid)
    for start in range(0, height, rows):
        stop = min(start + rows, height)
        band = np.stack([padded[dy + start:dy + stop, dx:dx + width]
                         for dy, dx in offsets])
        result[start:stop] = np.median(band, axis=0)
    return result


def _suspect(grid):
    """Masque des mailles qui ne peuvent pas etre du terrain.

    Deux criteres, parce qu'aucun ne suffit seul. Le premier est absolu et
    vaut partout : le point le plus bas de France metropolitaine est a
    environ -2 m, rien sous -10 m n'est du relief. Le second est relatif et
    rattrape le reste : une maille qui plonge de plus de 200 m sous la
    mediane d'un anneau a trois mailles n'est pas un versant, aucun terrain
    francais ne descendant si vite.

    Un marquage en trop ne coute presque rien, et c'est ce qui autorise un
    seuil franc : la reparation va rechercher la vraie altitude a maille
    fine, si bien qu'une maille marquee a tort est remplacee par sa propre
    valeur. On y perd une requete, pas de la justesse.
    """
    return (
        (grid < Z_MIN_PLAUSIBLE)
        | (grid > Z_MAX_PLAUSIBLE)
        | (grid < _ring_median(grid, SPIKE_RING_CELLS) - SPIKE_DROP)
    )


def _clusters(mask, pad=1):
    """Boites englobantes des amas de mailles marquees, en indices de maille.

    Les artefacts vont par petits amas - jusqu'a vingt-quatre mailles
    observees - et c'est par amas qu'on ira rechercher la donnee, une requete
    valant pour tout l'amas plutot qu'une par maille.
    """
    height, width = mask.shape
    seen = np.zeros_like(mask)
    boxes = []
    for row, col in zip(*np.nonzero(mask)):
        if seen[row, col]:
            continue
        stack = [(row, col)]
        seen[row, col] = True
        top = bottom = row
        left = right = col
        while stack:
            y, x = stack.pop()
            top, bottom = min(top, y), max(bottom, y)
            left, right = min(left, x), max(right, x)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if (0 <= ny < height and 0 <= nx < width
                            and mask[ny, nx] and not seen[ny, nx]):
                        seen[ny, nx] = True
                        stack.append((ny, nx))
        boxes.append((max(0, top - pad), max(0, left - pad),
                      min(height - 1, bottom + pad),
                      min(width - 1, right + pad)))
    return boxes


def _finer_steps(resolution):
    """Mailles de secours, de la plus proche a la plus fine.

    Seules celles qui divisent la maille courante en un nombre entier de
    sous-mailles sont retenues : le recalage se fait par blocs, et un bloc a
    cheval sur deux mailles ne serait pas moyennable proprement.
    """
    steps = []
    for step in sorted(RESOLUTION_STEPS, reverse=True):
        if step >= resolution:
            continue
        factor = resolution / step
        if abs(factor - round(factor)) < 1e-9:
            steps.append(step)
    return steps


def _resample_patch(box, origin, resolution, fine, layer, timeout=None):
    """Redemande une portion du MNT a maille fine et la ramene a la maille
    courante par moyenne de blocs.

    C'est la reponse juste aux valeurs aberrantes, et elle tient a ce qu'on a
    mesure : le meme kilometre carre rend -97,4 m a 50 m de maille et 371,4 m
    a 5 m. La donnee correcte existe, le service la sert, seul son
    rééchantillonnage vers les mailles grossieres la corrompt. Autant aller
    la chercher plutot que de la deviner a partir des voisines.

    Renvoie le tableau a la maille courante, ou None si la portion est trop
    grande pour une requete.
    """
    top, left, bottom, right = box
    rows = bottom - top + 1
    cols = right - left + 1
    factor = int(round(resolution / fine))
    if rows * factor > WMS_MAX_PIXELS or cols * factor > WMS_MAX_PIXELS:
        return None

    xmin = origin[0] + left * resolution
    ymax = origin[1] - top * resolution
    patch_bbox = (xmin, ymax - rows * resolution,
                  xmin + cols * resolution, ymax)
    payload = wms_bil(patch_bbox, cols * factor, rows * factor, layer=layer)
    fine_grid = np.frombuffer(payload, dtype=BIL_DTYPE).reshape(
        rows * factor, cols * factor
    )

    # La maille fine est saine bien plus souvent que la grossiere, mais pas
    # toujours : au meme endroit, le service rend 569 m a 25 m de maille et
    # -7434 m a 5 m. Les sous-mailles aberrantes sont donc ecartees avant la
    # moyenne, sans quoi une seule d'entre elles suffirait a tirer le bloc
    # vers le bas et a fabriquer une altitude fausse mais plausible - la
    # pire des deux, puisque plus rien ensuite ne la signale.
    valid = ((fine_grid >= Z_MIN_PLAUSIBLE) & (fine_grid <= Z_MAX_PLAUSIBLE))
    blocks = fine_grid.reshape(rows, factor, cols, factor)
    kept = valid.reshape(rows, factor, cols, factor)
    counts = kept.sum(axis=(1, 3))
    totals = np.where(kept, blocks, 0.0).sum(axis=(1, 3))

    # Un bloc entierement aberrant n'a rien a offrir : on le rend hors bornes
    # pour qu'il reste marque et parte a l'echelon suivant.
    return np.where(counts > 0, totals / np.maximum(counts, 1), NODATA)


def _repair(band, origin, resolution, layer, report=None):
    """Corrige les altitudes aberrantes du raster assemble.

    Deux moyens, dans cet ordre. On redemande d'abord la portion fautive a
    une maille plus fine, ou la donnee est saine, et on la ramene a la maille
    courante : c'est la vraie altitude, pas une estimation. Si le doute
    persiste jusqu'a la maille la plus fine, on comble par interpolation
    depuis les voisines.

    Le comblement, et surtout pas le trou. La nuance est decisive : ces
    mailles sont a basse altitude, donc dans le fond de vallee, donc sur le
    lit du cours d'eau. Un trou pose la coupe l'ecoulement et ampute le
    bassin de tout ce qui se trouve a l'amont - mesure sur l'Allier a Vichy,
    8 394 km2 au lieu de 9 008, et la part du reseau amont contenue dans le
    bassin tombee de 100 a 93 %.

    Renvoie le nombre de mailles corrigees.
    """
    grid = band.ReadAsArray()
    mask = _suspect(grid)
    total = int(mask.sum())
    if not total:
        return 0

    resolved = 0
    for fine in _finer_steps(resolution):
        boxes = _clusters(mask)
        if not boxes:
            break
        for box in boxes:
            top, left, bottom, right = box
            try:
                patch = _resample_patch(box, origin, resolution, fine, layer)
            except GeoserviceError:
                continue
            if patch is None:
                continue
            window = grid[top:bottom + 1, left:right + 1]
            broken = mask[top:bottom + 1, left:right + 1]
            healthy = ((patch >= Z_MIN_PLAUSIBLE)
                       & (patch <= Z_MAX_PLAUSIBLE))
            take = broken & healthy
            window[take] = patch[take]
            broken &= ~healthy
        band.WriteArray(grid)
        band.FlushCache()
        mask = _suspect(band.ReadAsArray())
        grid = band.ReadAsArray()
        resolved = total - int(mask.sum())
        if not mask.any():
            if report is not None:
                report("  {0} maille(s) aberrante(s) corrigee(s) en "
                       "redemandant le MNT a {1:.0f} m.".format(total, fine))
            return total

    # Le doute persiste : on comble depuis les voisines, faute de mieux.
    remaining = int(mask.sum())
    grid[mask] = NODATA
    band.WriteArray(grid)
    band.FlushCache()
    gdal.FillNodata(band, None, FILL_SEARCH_CELLS, 0)
    band.FlushCache()
    if report is not None:
        report("  {0} maille(s) aberrante(s) : {1} reprise(s) a maille fine, "
               "{2} comblee(s) par interpolation.".format(
                   total, resolved, remaining))
    return total


def download_dem(bbox, output_path, resolution=None, layer=LAYER_DEM,
                 max_pixels=None, progress=None):
    """Telecharge le MNT sur l'emprise et l'ecrit en GeoTIFF Float32.

    resolution vaut None pour laisser la maille s'ajuster a l'emprise et a la
    memoire disponible ; une valeur explicite est respectee telle quelle, mais
    reste soumise au plafond de mailles.

    Renvoie un dictionnaire decrivant le raster produit.
    """
    def report(message):
        if progress is not None:
            progress(message)

    ceiling = max_pixels if max_pixels is not None else max_pixels_for_memory()
    area_km2 = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]) / 1e6

    if resolution is None:
        resolution, count, ceiling = choose_resolution(bbox, ceiling)
        if resolution != RESOLUTION_STEPS[0]:
            report(
                "Emprise de {0:.0f} km2 : maille portee a {1:.0f} m pour "
                "tenir dans la memoire disponible ({2:.1f} Mpx au lieu de "
                "{3:.1f}).".format(
                    area_km2, resolution, count / 1e6,
                    pixel_count(bbox, RESOLUTION_STEPS[0]) / 1e6)
            )

    snapped, width, height = snap_bbox(bbox, resolution)
    xmin, ymin, xmax, ymax = snapped

    total_pixels = width * height
    report("MNT : {0} x {1} px a {2:.0f} m ({3:.1f} Mpx)".format(
        width, height, resolution, total_pixels / 1e6))
    if total_pixels > ceiling:
        raise DemError(
            "Emprise de {0:.0f} km2 : meme a {1:.0f} m de maille, le calcul "
            "demanderait {2:.0f} millions de mailles alors que la memoire "
            "disponible n'en permet que {3:.0f}. Fermez des applications, ou "
            "choisissez un exutoire plus en amont.".format(
                area_km2, resolution, total_pixels / 1e6, ceiling / 1e6)
        )

    driver = gdal.GetDriverByName("GTiff")
    dataset = driver.Create(
        output_path, width, height, 1, gdal.GDT_Float32,
        options=["COMPRESS=DEFLATE", "PREDICTOR=3", "TILED=YES"],
    )
    if dataset is None:
        raise DemError("Creation impossible du fichier {0}".format(output_path))

    dataset.SetGeoTransform((xmin, resolution, 0.0, ymax, 0.0, -resolution))
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(LAMBERT93_EPSG)
    dataset.SetProjection(srs.ExportToWkt())
    band = dataset.GetRasterBand(1)
    band.SetNoDataValue(NODATA)

    tiles = list(_tiles(width, height, WMS_MAX_PIXELS))
    for index, (col, row, tile_width, tile_height) in enumerate(tiles, 1):
        tile_bbox = (
            xmin + col * resolution,
            ymax - (row + tile_height) * resolution,
            xmin + (col + tile_width) * resolution,
            ymax - row * resolution,
        )
        if len(tiles) > 1:
            report("  dalle {0}/{1}".format(index, len(tiles)))
        payload = wms_bil(tile_bbox, tile_width, tile_height, layer=layer)
        rows = _unpack(payload, tile_width, tile_height)
        for offset, line in enumerate(rows):
            band.WriteRaster(
                col, row + offset, tile_width, 1,
                struct.pack("<{0}f".format(tile_width), *line),
                buf_type=gdal.GDT_Float32,
            )

    band.FlushCache()
    voids = _repair(band, (xmin, ymax), resolution, layer, report)
    stats = band.ComputeStatistics(False)
    dataset = None  # ferme et ecrit le fichier

    report("MNT ecrit : altitudes de {0:.1f} a {1:.1f} m".format(
        stats[0], stats[1]))
    if stats[1] <= stats[0]:
        raise DemError("MNT constant : la couche interrogee est probablement "
                       "hors emprise de couverture.")

    return {
        "path": output_path,
        "bbox": snapped,
        "width": width,
        "height": height,
        "resolution": resolution,
        "z_min": stats[0],
        "z_max": stats[1],
        "z_mean": stats[2],
        "size_mb": os.path.getsize(output_path) / 1e6,
        "mailles_comblees": voids,
    }
