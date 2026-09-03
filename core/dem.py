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

from osgeo import gdal, osr

from .geoservices import LAYER_DEM, WMS_MAX_PIXELS, wms_bil

DEFAULT_RESOLUTION = 5.0  # RGE ALTI 5 m
NODATA = -99999.0
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
    }
