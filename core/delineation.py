# -*- coding: utf-8 -*-
"""Delimitation du bassin versant a partir du MNT, via GRASS.

Enchainement :
    r.watershed      directions d'ecoulement + accumulation
    recalage         l'exutoire est ramene sur la maille de plus fort drainage
    r.water.outlet   raster binaire du bassin
    polygonisation   passage en vecteur, nettoyage, simplification

Le recalage est l'etape critique. Le point accroche sur la BD TOPO tombe sur
le trace cartographique du cours d'eau, qui ne coincide pas forcement, a la
maille pres, avec le talweg deduit du MNT. Quelques metres d'ecart suffisent a
sortir un bassin de quelques ares au lieu de plusieurs kilometres carres : on
cherche donc, dans un petit voisinage, la maille ou l'accumulation est
maximale.
"""

import math
import os

import numpy as np
import processing
from osgeo import gdal
from qgis.core import (
    QgsFeature, QgsFeatureRequest, QgsGeometry, QgsVectorLayer,
)

# GRASS est expose sous deux identifiants selon les versions de QGIS.
GRASS_PREFIXES = ("grass7:", "grass:")

# Rayon de recherche du talweg autour de l'exutoire accroche, en metres.
# Exprime en metres et non en mailles : la distance qui separe le trace
# cartographique du talweg calcule ne depend pas de la finesse du MNT.
SNAP_RADIUS = 50.0

# Densite de drainage maximale retenue pour borner le recalage, en km de
# cours d'eau par km2 de bassin.
#
# Elle sert a traduire ce que la BD TOPO nous apprend en une surface minimale
# plausible : un cours d'eau qui porte quinze kilometres d'affluents cartes ne
# peut pas drainer un demi-hectare. En France, la densite de drainage va de
# 0,5 a 2 km/km2 ; on retient 5, tres large, pour que la borne n'ecarte que
# l'absurde et jamais un bassin reel.
MAX_DRAINAGE_DENSITY = 5.0

# Points testes pour le controle de stabilite : les huit voisins a un pas de
# maille, soit un disque d'environ deux mailles de diametre autour de
# l'exutoire retenu - la precision reelle d'un clic sur la carte.
STABILITY_OFFSETS = ((1, 0), (-1, 0), (0, 1), (0, -1),
                      (1, 1), (1, -1), (-1, 1), (-1, -1))

# Recouvrement (intersection sur union) en-deca duquel un voisin est repute
# diverger du bassin retenu plutot que d'en etre une simple variante.
#
# Mesure sur un cas reel ou l'exutoire tombait a quelques metres d'une ligne
# de partage franche (une mare et le vallon qu'elle masquait) : huit voisins
# sur neuf rendaient un bassin de 2,7 a 3,0 ha, le neuvieme 49,7 ha - une
# intersection quasi nulle. 0.5 laisse passer le glissement normal d'un
# vallon etroit tout en attrapant ce genre de bascule.
STABILITY_MIN_IOU = 0.5

# Rayon maximal de recherche du talweg, en metres.
#
# Le rayon nominal double tant qu'aucun chenal recevable n'est a portee. Il
# faut aller loin : sur le Darot, affluent de l'Allier, le talweg qui draine
# ses quinze kilometres carres se trouve a 183 m du trace BD TOPO, l'ecart
# etant celui d'une plaine alluviale ou le lit carte et le lit calcule ne
# coincident pas. Au-dela de quatre cents metres, en revanche, ce n'est plus
# un ecart de trace : on n'est pas sur le bon cours d'eau.
MAX_SNAP_RADIUS = 400.0

# Encodage des directions d ecoulement de r.watershed, en deplacements
# (ligne, colonne). Les lignes croissent vers le sud.
#
#     3 2 1
#     4 . 8
#     5 6 7
#
# Zero marque une cuvette et les valeurs negatives une maille qui s ecoule
# hors de la region : dans les deux cas la descente s arrete.
DRAINAGE_MOVES = {
    1: (-1, 1), 2: (-1, 0), 3: (-1, -1), 4: (0, -1),
    5: (1, -1), 6: (1, 0), 7: (1, 1), 8: (0, 1),
}

# Ecart maximal accepte entre le trace carte et le chenal du MNT pour poser
# un point d accroche. Il est volontairement serre : on ne s accroche que la
# ou les deux coincident franchement, en tete de bassin.
MATCH_TOLERANCE = 30.0

# Part du reseau amont qui doit se retrouver dans le bassin pour qu'il soit
# tenu pour confirme. En deca, la seconde approche est tentee.
CONTAINMENT_MIN = 0.6

# Nombre maximal de mailles parcourues en descendant l ecoulement. Un bassin
# de neuf mille kilometres carres a 50 m de maille fait moins de dix mille
# mailles de long ; la borne n arrete qu une anomalie.
DESCENT_LIMIT = 200000

# Seuil de r.watershed : nombre minimal de mailles drainees pour ouvrir un
# cours d'eau. 200 mailles de 5 m font 0,5 ha, ce qui donne un chevelu dense
# sans bruit excessif.
STREAM_THRESHOLD = 200

# Tolerance de simplification du contour, en nombre de mailles.
#
# Le polygone issu de la rasterisation suit les bords de maille : son contour
# est un escalier qui allonge le perimetre d'environ 30 % sans rien changer a
# la surface. Comme l'indice de Gravelius est proportionnel au perimetre, il
# est alors surestime d'autant : 1,73 au lieu de 1,30 sur un bassin d'essai.
# Deux mailles de tolerance suffisent a retrouver un contour credible, en
# faisant varier la surface de moins de 0,05 %.
SIMPLIFY_CELLS = 2.0


class DelineationError(RuntimeError):
    """Le bassin versant n'a pas pu etre delimite."""


def _algorithm(name):
    """Renvoie l'identifiant GRASS disponible dans cette installation."""
    from qgis.core import QgsApplication
    registry = QgsApplication.processingRegistry()
    for prefix in GRASS_PREFIXES:
        if registry.algorithmById(prefix + name) is not None:
            return prefix + name
    raise DelineationError(
        "L'algorithme GRASS {0} est introuvable. Verifiez que le fournisseur "
        "GRASS est actif dans les options de Processing.".format(name)
    )


def _window_around(dataset, x, y, radius_m):
    """Fenetre de lecture centree sur un point, de rayon donne en metres."""
    origin_x, pixel_x, _, origin_y, _, pixel_y = dataset.GetGeoTransform()
    cell = abs(pixel_x)
    radius = max(1, int(round(radius_m / cell)))
    col = int((x - origin_x) / pixel_x)
    row = int((y - origin_y) / pixel_y)
    col_min = max(0, col - radius)
    row_min = max(0, row - radius)
    col_max = min(dataset.RasterXSize - 1, col + radius)
    row_max = min(dataset.RasterYSize - 1, row + radius)
    if col_max < col_min or row_max < row_min:
        raise DelineationError("L'exutoire tombe hors du MNT telecharge.")
    return (col_min, row_min, col_max - col_min + 1, row_max - row_min + 1)


def snap_to_thalweg(streams_path, accumulation_path, x, y,
                    radius_m=SNAP_RADIUS, min_drained_cells=0.0):
    """Ramene l'exutoire sur le talweg du cours d'eau designe.

    Le trace cartographique d'un cours d'eau et le talweg calcule a partir du
    MNT ne se superposent pas : en fond de vallee alluviale, l'ecart depasse
    couramment la centaine de metres. Un exutoire laisse a cote du talweg
    draine alors une poignee de mailles de versant, et le bassin obtenu n'a
    plus rien a voir avec celui qu'on cherchait.

    Trois regles, dans cet ordre.

    **Le plus proche, et non le plus draine.** On respecte ainsi le cours
    d'eau que l'utilisateur a designe : prendre le maximum d'accumulation
    ferait sauter l'exutoire sur la riviere voisine des qu'elle passe a
    portee. A egale distance, la maille la plus drainee l'emporte, ce qui
    departage les deux rives d'un meme chenal.

    **Parmi ceux qui peuvent etre le bon.** La proximite seule ne dit pas
    *quel* chenal on cherche : pres d'une confluence, un ravin de quelques
    ares passe souvent plus pres du trace carte que le talweg voulu. Sur le
    Gourcet, affluent de l'Allier, six cent vingt-cinq mailles de chenal se
    trouvaient a moins de soixante metres, la plus proche drainant un
    centieme de kilometre carre quand le talweg cherche en drainait seize.
    min_drained_cells, deduit du lineaire deja connu de la BD TOPO, ecarte
    ces chenaux-la.

    **Et dont le bassin tient dans le MNT.** GRASS compte negativement les
    mailles dont une partie du bassin sort de la region calculee : ce sont
    les cours d'eau qui viennent d'ailleurs, l'Allier traversant l'emprise
    d'un de ses affluents par exemple. Leur bassin n'est de toute facon pas
    calculable ici, et les ecarter permet d'elargir la recherche sans risquer
    de sauter dessus.

    La recherche s'elargit en effet tant qu'aucun chenal recevable n'est a
    portee, jusqu'a MAX_SNAP_RADIUS. C'est necessaire : sur le Darot, autre
    affluent de l'Allier, le talweg qui draine ses quinze kilometres carres
    se trouve a cent quatre-vingt-trois metres du trace BD TOPO.

    Renvoie un dictionnaire : x, y, accumulation, decalage, et la facon dont
    le point a ete retenu.
    """
    streams_ds = gdal.Open(streams_path)
    accumulation_ds = gdal.Open(accumulation_path)
    if streams_ds is None or accumulation_ds is None:
        raise DelineationError("Rasters d'ecoulement illisibles.")
    transform = streams_ds.GetGeoTransform()
    origin_x, pixel_x, _, origin_y, _, pixel_y = transform

    def read(radius):
        """Chenaux et accumulation autour du point, dans le rayon donne."""
        window = _window_around(streams_ds, x, y, radius)
        band = streams_ds.GetRasterBand(1)
        nodata = band.GetNoDataValue()
        streams = band.ReadAsArray(*window)
        # Le signe est conserve : il porte l'information "bassin complet".
        accumulation = accumulation_ds.GetRasterBand(1).ReadAsArray(*window)
        if streams is None or accumulation is None:
            raise DelineationError("Lecture impossible autour de l'exutoire.")
        channel = np.isfinite(streams) & (streams > 0)
        if nodata is not None:
            channel &= streams != nodata
        return window, channel, accumulation

    def pick(window, mask, accumulation):
        """Maille la plus proche du point parmi celles du masque."""
        col_min, row_min = window[0], window[1]
        rows, cols = np.nonzero(mask)
        xs = origin_x + (col_min + cols + 0.5) * pixel_x
        ys = origin_y + (row_min + rows + 0.5) * pixel_y
        distances = np.hypot(xs - x, ys - y)
        drained = np.abs(accumulation[rows, cols])
        # Tri par distance, puis par drainage decroissant a distance egale.
        order = np.lexsort((-drained, np.round(distances / abs(pixel_x))))
        best = order[0]
        return int(rows[best]), int(cols[best])

    radii = []
    radius = float(radius_m)
    while True:
        radii.append(radius)
        if radius >= MAX_SNAP_RADIUS:
            break
        radius = min(radius * 2.0, MAX_SNAP_RADIUS)

    chosen = window = accumulation = None
    origin = "chevelu"
    for radius in radii:
        window, channel, accumulation = read(radius)
        eligible = channel & (accumulation > 0)
        if min_drained_cells > 0:
            eligible &= accumulation >= min_drained_cells
        if eligible.any():
            chosen = pick(window, eligible, accumulation)
            if radius > radius_m:
                origin = "chevelu, a {0:.0f} m de recherche".format(radius)
            break

    if chosen is None:
        # Aucun chenal recevable, meme au plus large. On retombe sur le plus
        # proche chenal du rayon nominal, et a defaut sur la maille la plus
        # drainee : le controle de contenance, en aval, dira si le resultat
        # tient debout.
        window, channel, accumulation = read(radius_m)
        if channel.any():
            chosen = pick(window, channel, accumulation)
            origin = "chevelu, sans confirmation"
        else:
            flat = int(np.argmax(np.abs(accumulation)))
            chosen = divmod(flat, window[2])
            origin = "accumulation maximale"

    streams_ds = accumulation_ds = None
    col_min, row_min = window[0], window[1]
    row, col = chosen
    snapped_x = origin_x + (col_min + col + 0.5) * pixel_x
    snapped_y = origin_y + (row_min + row + 0.5) * pixel_y
    return {
        "x": snapped_x,
        "y": snapped_y,
        "accumulation": float(abs(accumulation[row, col])),
        "shift": math.hypot(snapped_x - x, snapped_y - y),
        "origine": origin,
    }


def minimum_drained_area(upstream_km):
    """Surface minimale plausible, en m2, pour un reseau amont de cette
    longueur. Renvoie 0 quand le lineaire est inconnu."""
    if not upstream_km:
        return 0.0
    return upstream_km / MAX_DRAINAGE_DENSITY * 1e6


def _descend(drainage, row, col, x, y, transform, limit=DESCENT_LIMIT):
    """Suit les fleches d'ecoulement depuis une maille, vers l'aval.

    Renvoie la maille du trajet la plus proche de (x, y), c'est-a-dire le
    point ou l'ecoulement passe au plus pres de l'exutoire demande. Le trajet
    s'arrete s'il sort du raster, tombe sur une cuvette, ou boucle.
    """
    origin_x, pixel_x, _, origin_y, _, pixel_y = transform
    height, width = drainage.shape
    best = None
    seen = set()
    for _step in range(limit):
        if not (0 <= row < height and 0 <= col < width):
            break
        if (row, col) in seen:
            break
        seen.add((row, col))
        cell_x = origin_x + (col + 0.5) * pixel_x
        cell_y = origin_y + (row + 0.5) * pixel_y
        distance = math.hypot(cell_x - x, cell_y - y)
        if best is None or distance < best[0]:
            best = (distance, row, col)
        move = DRAINAGE_MOVES.get(int(drainage[row, col]))
        if move is None:
            break
        row, col = row + move[0], col + move[1]
    return best


def snap_by_descent(streams_path, accumulation_path, drainage_path,
                    upstream, x, y, min_drained_cells=0.0):
    """Trouve l'exutoire en suivant l'ecoulement depuis l'amont.

    C'est le recours quand la recherche par voisinage a designe le mauvais
    chenal. Elle est aveugle par nature : elle regarde autour d'un point et
    ne sait pas ou va l'eau. Ici on procede a l'envers, et on se sert de ce
    que la BD TOPO nous a deja appris.

    Le principe tient a une dissymetrie du terrain. En tete de bassin, la
    vallee est encaissee : le lit carte et le lit que le MNT reconstitue
    coincident a quelques metres. En plaine alluviale, ils divergent de
    plusieurs centaines de metres, chacun suivant un ancien bras ou un fosse
    different - c'est justement pres des confluences, ou tombent les
    exutoires, que la correspondance est la plus mauvaise.

    On s'accroche donc la ou la correspondance est bonne, puis on laisse
    l'ecoulement faire le reste : depuis cette maille, on suit les fleches
    de proche en proche et on retient celle qui passe au plus pres du point
    demande. L'exutoire est alors trouve par l'ecoulement lui-meme, et non
    par un rayon de recherche.

    Renvoie un dictionnaire de meme forme que snap_to_thalweg, ou None si
    aucun point d'accroche fiable n'a ete trouve.
    """
    streams_ds = gdal.Open(streams_path)
    accumulation_ds = gdal.Open(accumulation_path)
    drainage_ds = gdal.Open(drainage_path)
    if None in (streams_ds, accumulation_ds, drainage_ds):
        return None
    transform = streams_ds.GetGeoTransform()
    origin_x, pixel_x, _, origin_y, _, pixel_y = transform
    cell = abs(pixel_x)

    streams_band = streams_ds.GetRasterBand(1)
    nodata = streams_band.GetNoDataValue()
    streams = streams_band.ReadAsArray()
    accumulation = accumulation_ds.GetRasterBand(1).ReadAsArray()
    drainage = drainage_ds.GetRasterBand(1).ReadAsArray()
    streams_ds = accumulation_ds = drainage_ds = None
    if streams is None or accumulation is None or drainage is None:
        return None

    height, width = streams.shape
    channel = np.isfinite(streams) & (streams > 0) & (accumulation > 0)
    if nodata is not None:
        channel &= streams != nodata
    if min_drained_cells > 0:
        channel &= accumulation >= min_drained_cells
    if not channel.any():
        return None

    # Point d'accroche : la maille de chenal la mieux drainee parmi celles qui
    # collent vraiment au trace carte. Le plus draine, car plus on s'accroche
    # bas, plus la descente est courte et sure ; mais seulement parmi les
    # correspondances franches, a MATCH_TOLERANCE pres.
    reach = max(1, int(round(MATCH_TOLERANCE / cell)))
    anchor = None
    for record in upstream:
        geometry = record["geometry"]
        length = geometry.length()
        if length <= 0:
            continue
        for share in (0.25, 0.5, 0.75):
            point = geometry.interpolate(length * share).asPoint()
            col = int((point.x() - origin_x) / pixel_x)
            row = int((point.y() - origin_y) / pixel_y)
            top, bottom = max(0, row - reach), min(height, row + reach + 1)
            left, right = max(0, col - reach), min(width, col + reach + 1)
            window = channel[top:bottom, left:right]
            if not window.any():
                continue
            rows, cols = np.nonzero(window)
            drained = accumulation[top + rows, left + cols]
            best = int(np.argmax(drained))
            score = float(drained[best])
            if anchor is None or score > anchor[0]:
                anchor = (score, int(top + rows[best]), int(left + cols[best]))
    if anchor is None:
        return None

    found = _descend(drainage, anchor[1], anchor[2], x, y, transform)
    if found is None:
        return None
    distance, row, col = found
    snapped_x = origin_x + (col + 0.5) * pixel_x
    snapped_y = origin_y + (row + 0.5) * pixel_y
    return {
        "x": snapped_x,
        "y": snapped_y,
        "accumulation": float(abs(accumulation[row, col])),
        "shift": math.hypot(snapped_x - x, snapped_y - y),
        "origine": "descente depuis l'amont",
        "approche": distance,
    }


def delineate(dem_info, outlet, workdir, threshold=STREAM_THRESHOLD,
              snap_radius=SNAP_RADIUS, simplify_cells=SIMPLIFY_CELLS,
              upstream_km=0.0, upstream=None, validate=None,
              progress=None, feedback=None):
    """Delimite le bassin versant draine par l'exutoire.

    dem_info est le dictionnaire renvoye par core.dem.download_dem.

    upstream et validate servent la seconde tentative : le reseau amont connu
    de la BD TOPO, et un appelable qui rend la part de ce reseau contenue
    dans un bassin propose, entre 0 et 1. Quand le premier recalage produit
    un bassin que ce controle refuse, l'exutoire est recherche autrement, en
    suivant l'ecoulement depuis l'amont.
    Renvoie un dictionnaire decrivant le resultat, dont la geometrie du
    bassin (QgsGeometry) et le chemin du GeoPackage produit.
    """
    def report(message):
        if progress is not None:
            progress(message)

    os.makedirs(workdir, exist_ok=True)
    cellsize = dem_info["resolution"]
    # La region GRASS n'est pas imposee : par defaut elle epouse le raster
    # d'entree, qui est deja exactement l'emprise voulue. Une region donnee a
    # la main est une source d'erreur silencieuse - un ordre de coordonnees
    # inverse produit une region de plusieurs millions de lignes et un echec
    # d'allocation memoire, sans message exploitable.

    accumulation = os.path.join(workdir, "accumulation.tif")
    drainage = os.path.join(workdir, "drainage.tif")
    streams = os.path.join(workdir, "streams.tif")

    report("Ecoulements et accumulation (r.watershed)...")
    # Ecoulement simple (-s), et non le multiple par defaut.
    #
    # r.water.outlet, qui extrait le bassin, ne connait pas le chevelu : il ne
    # lit que la carte des directions, ou chaque maille pointe vers une seule
    # voisine, et remonte ces fleches a l'envers depuis l'exutoire. Or en
    # ecoulement multiple, l'accumulation repartit le flux entre plusieurs
    # voisines pendant que la carte des directions n'en retient qu'une : les
    # deux ne mesurent plus la meme chose. Une maille peut alors etre un gros
    # chenal selon l'accumulation et ne rien drainer quand on suit les
    # fleches.
    #
    # Ce n'est pas une subtilite theorique. A l'embouchure du Gourcet dans la
    # vallee de l'Allier, ou le relief est plat, l'accumulation annoncait
    # 5,47 km2 la ou l'extraction rendait 1,02 ha - un facteur cinq cents, et
    # un echec. En ecoulement simple, les trois sorties viennent du meme
    # routage : 16,31 km2 annonces, 16,307 extraits.
    #
    # Le cout est negligeable, mesure sur quatre bassins de 33 a 9 008 km2 :
    # les surfaces bougent de 0,006 a 0,03 %.
    #
    # Les autres indicateurs booleens ne sont pas transmis : passes a False
    # ils font echouer l'algorithme sans message.
    watershed = processing.run(_algorithm("r.watershed"), {
        "elevation": dem_info["path"],
        "threshold": threshold,
        "accumulation": accumulation,
        "drainage": drainage,
        "stream": streams,
        "-s": True,
        "GRASS_REGION_CELLSIZE_PARAMETER": 0,
    }, feedback=feedback)
    accumulation = watershed["accumulation"]
    drainage = watershed["drainage"]
    streams = watershed["stream"]

    cell_area = cellsize * cellsize

    def extract(candidate, tag):
        """Extrait le bassin draine par un exutoire recale.

        Renvoie (geometrie, raster) ou (None, motif) quand le bassin obtenu
        n'est pas recevable. Les rasters d'ecoulement etant deja calcules,
        une tentative supplementaire ne coute que l'extraction et la
        vectorisation, quelques secondes.
        """
        point = (candidate["x"], candidate["y"])
        raster = processing.run(_algorithm("r.water.outlet"), {
            "input": drainage,
            "coordinates": "{0},{1}".format(*point),
            "output": os.path.join(workdir, "basin{0}.tif".format(tag)),
            "GRASS_REGION_CELLSIZE_PARAMETER": 0,
        }, feedback=feedback)["output"]
        vectors = processing.run("gdal:polygonize", {
            "INPUT": raster,
            "BAND": 1,
            "FIELD": "value",
            "EIGHTCONNECTEDNESS": True,
            "OUTPUT": os.path.join(workdir, "basin_raw{0}.gpkg".format(tag)),
        }, feedback=feedback)["OUTPUT"]

        shape = _largest_polygon(vectors)
        if shape is None:
            return None, ("Aucun bassin versant n'a pu etre extrait. "
                          "L'exutoire est probablement hors du reseau "
                          "d'ecoulement.")

        surface = shape.area()
        # Le raster d'accumulation annonce combien de mailles se deversent
        # dans l'exutoire : le polygone doit retrouver a peu pres cette
        # surface. Un ecart important signale que le point est tombe a cote
        # du talweg, ce qu'un simple seuil en valeur absolue ne detecte pas -
        # un bassin de 600 m2 est absurde pour une riviere et parfaitement
        # normal pour un fosse.
        expected = candidate["accumulation"] * cell_area
        if expected > 0 and surface < 0.5 * expected:
            return None, (
                "Bassin incoherent : {0:.2f} ha extraits alors que "
                "l'exutoire draine {1:.2f} ha d'apres le modele de "
                "terrain.".format(surface / 1e4, expected / 1e4))
        if surface < 20 * cell_area:
            return None, (
                "Bassin degenere ({0:.0f} m2, {1:.0f} mailles) : l'exutoire "
                "n'est pas tombe sur un talweg. Augmentez le rayon "
                "d'accrochage ou deplacez le point.".format(
                    surface, surface / cell_area))
        return (shape, raster), None

    def announce(candidate):
        report("  decale de {0:.1f} m ({1}) : {2:.0f} mailles drainees, "
               "soit {3:.2f} km2".format(
                   candidate["shift"], candidate["origine"],
                   candidate["accumulation"],
                   candidate["accumulation"] * cell_area / 1e6))

    def stability_check(geometry, click_x, click_y, min_drained_cells):
        """Le bassin retenu tient-il face a un leger deplacement du clic ?

        Sans reseau amont connu, rien d'autre ne dit si l'exutoire est tombe
        pres d'une ligne de partage des eaux : deux clics separes de
        quelques metres peuvent se recaler sur des bassins entierement
        differents. On rejoue donc le recalage complet (pas seulement
        l'extraction) pour huit clics voisins, a un pas de maille autour du
        point clique d'origine - et non du point deja recale, qui a deja
        tranche l'ambiguite en se figeant d'un cote de la ligne de partage.
        Chaque candidat est compare au resultat retenu par intersection sur
        union - moins sensible qu'un simple rapport de surfaces, que deux
        bassins de meme taille mais disjoints tromperait.

        Renvoie le plus mauvais recouvrement observe (1.0 si tous les
        voisins rendent essentiellement le meme bassin) et, quand il tombe
        sous STABILITY_MIN_IOU, la surface du voisin qui diverge.
        """
        base_area = geometry.area()
        worst_iou = 1.0
        worst_area = None
        for index, (dcol, drow) in enumerate(STABILITY_OFFSETS):
            nearby = snap_to_thalweg(
                streams, accumulation,
                click_x + dcol * cellsize, click_y + drow * cellsize,
                snap_radius, min_drained_cells,
            )
            neighbour, _refusal = extract(nearby, "_stab{0}".format(index))
            if neighbour is None:
                continue
            other = neighbour[0]
            intersection = geometry.intersection(other).area()
            union = base_area + other.area() - intersection
            iou = intersection / union if union > 0 else 0.0
            if iou < worst_iou:
                worst_iou = iou
                worst_area = other.area()
        return worst_iou, worst_area

    # Surface minimale plausible, deduite du lineaire deja carte : elle
    # ecarte les chenaux trop petits pour etre celui qu'on a designe.
    minimum = minimum_drained_area(upstream_km) / cell_area

    report("Recalage de l'exutoire sur le talweg...")
    snapped = snap_to_thalweg(streams, accumulation, outlet[0], outlet[1],
                              snap_radius, minimum)
    announce(snapped)
    report("Extraction du bassin (r.water.outlet)...")
    produced, refusal = extract(snapped, "")
    trust = None if produced is None else (
        validate(produced[0]) if validate is not None else None
    )

    # Seconde tentative, guidee par l'ecoulement.
    #
    # La recherche par voisinage est aveugle : elle regarde autour du point
    # et ne sait pas ou va l'eau. Quand elle se trompe - et elle se trompe
    # pres des confluences, ou le trace carte et le talweg calcule divergent
    # de plusieurs centaines de metres - on reprend le probleme par l'amont,
    # la ou les deux coincident, et on laisse l'ecoulement designer
    # l'exutoire. Voir snap_by_descent.
    #
    # Elle n'est tentee qu'en cas d'echec, et ne remplace le premier resultat
    # que si elle fait mieux : le chemin qui fonctionne reste premier.
    if upstream and (produced is None or (trust is not None
                                          and trust < CONTAINMENT_MIN)):
        report("Bassin non confirme : reprise en suivant l'ecoulement "
               "depuis l'amont...")
        second = snap_by_descent(streams, accumulation, drainage, upstream,
                                 outlet[0], outlet[1], minimum)
        if second is not None:
            announce(second)
            other, other_refusal = extract(second, "_amont")
            other_trust = None if other is None else (
                validate(other[0]) if validate is not None else None
            )
            better = other is not None and (
                produced is None
                or other_trust is None
                or trust is None
                or other_trust > trust
            )
            if better:
                snapped, produced, refusal = second, other, other_refusal
                trust = other_trust

    if produced is None:
        raise DelineationError(refusal)

    geometry, basin_raster = produced
    x, y = snapped["x"], snapped["y"]
    score = snapped["accumulation"]
    area = geometry.area()

    # Sans reseau amont, le controle de contenance ne peut rien dire (voir
    # network_containment) : c'est le seul autre signal qu'un exutoire tombe
    # pres d'une ligne de partage des eaux plutot que sur le bon talweg.
    stability = 1.0
    if not upstream:
        report("Controle de stabilite : huit exutoires voisins...")
        stability, unstable_area = stability_check(
            geometry, outlet[0], outlet[1], minimum)
        if stability < STABILITY_MIN_IOU:
            raise DelineationError(
                "Exutoire instable : un deplacement d'une seule maille "
                "suffit a faire basculer le bassin de {0:.2f} ha vers un "
                "autre de {1:.2f} ha (recouvrement {2:.0f} %). Le point est "
                "probablement pose pres d'une ligne de partage des eaux. "
                "Deplacez-le, meme de quelques metres.".format(
                    area / 1e4, unstable_area / 1e4, 100 * stability))

    raw_perimeter = geometry.length()
    if simplify_cells and simplify_cells > 0:
        tolerance = simplify_cells * cellsize
        simplified = geometry.simplify(tolerance)
        if not simplified.isEmpty() and simplified.isGeosValid():
            smoothed = simplified.smooth(1, 0.25)
            geometry = smoothed if (
                not smoothed.isEmpty() and smoothed.isGeosValid()
            ) else simplified
            area = geometry.area()
            report("Contour simplifie a {0:.0f} m : perimetre {1:.0f} m au "
                   "lieu de {2:.0f} m".format(
                       tolerance, geometry.length(), raw_perimeter))

    report("Bassin : {0:.3f} km2".format(area / 1e6))
    return {
        "geometry": geometry,
        "perimetre_brut_m": raw_perimeter,
        "tolerance_simplif_m": (simplify_cells or 0) * cellsize,
        "outlet": (x, y),
        "snap_shift": snapped["shift"],
        "snap_origin": snapped["origine"],
        "stabilite": stability,
        "accumulation_cells": score,
        "area": area,
        "perimeter": geometry.length(),
        "dem": dem_info,
        "rasters": {
            "accumulation": accumulation,
            "drainage": drainage,
            "streams": streams,
            "basin": basin_raster,
        },
    }


def _largest_polygon(gpkg_path):
    """Retient le plus grand polygone de valeur 1 et comble ses trous.

    La polygonisation produit un polygone par plage de valeurs ; le bassin
    porte la valeur 1. Les rares mailles isolees, artefacts de bordure, sont
    ecartees en ne gardant que la plus grande piece.
    """
    layer = QgsVectorLayer(gpkg_path, "basin", "ogr")
    if not layer.isValid():
        return None
    best = None
    request = QgsFeatureRequest()
    for feature in layer.getFeatures(request):
        if feature["value"] != 1:
            continue
        geometry = QgsGeometry(feature.geometry())
        if best is None or geometry.area() > best.area():
            best = geometry
    if best is None:
        return None
    # Comble les trous internes : un bassin versant est d'un seul tenant.
    filled = best.removeInteriorRings()
    return filled if isinstance(filled, QgsGeometry) else best
