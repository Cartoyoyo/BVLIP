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
                    radius_m=SNAP_RADIUS):
    """Ramene l'exutoire sur le chevelu deduit du MNT.

    Le trace cartographique d'un cours d'eau et le talweg calcule a partir du
    MNT ne se superposent pas toujours : en fond de vallee, l'ecart atteint
    couramment plusieurs dizaines de metres. Un exutoire laisse a cote du
    talweg draine alors une poignee de mailles de versant, et le bassin obtenu
    n'a plus rien a voir avec celui qu'on cherchait.

    On s'appuie donc sur le chevelu que r.watershed produit deja : les mailles
    qu'il retient sont, par construction, celles d'un vrai chenal. On prend la
    plus proche, et non la plus drainee, pour respecter le cours d'eau que
    l'utilisateur a designe : chercher le maximum d'accumulation dans un rayon
    de plusieurs dizaines de metres ferait sauter l'exutoire sur la riviere
    voisine des qu'elle passe a portee.

    A egale distance, la maille la plus drainee l'emporte : c'est ce qui
    departage les deux rives d'un meme chenal, et les abords d'une confluence.

    Renvoie un dictionnaire : x, y, accumulation, decalage, et la facon dont le
    point a ete retenu.
    """
    streams_ds = gdal.Open(streams_path)
    accumulation_ds = gdal.Open(accumulation_path)
    if streams_ds is None or accumulation_ds is None:
        raise DelineationError("Rasters d'ecoulement illisibles.")

    window = _window_around(streams_ds, x, y, radius_m)
    col_min, row_min, width, height = window
    transform = streams_ds.GetGeoTransform()
    origin_x, pixel_x, _, origin_y, _, pixel_y = transform

    streams_band = streams_ds.GetRasterBand(1)
    nodata = streams_band.GetNoDataValue()
    streams = streams_band.ReadAsArray(*window)
    # r.watershed compte negativement les mailles dont une partie du bassin
    # sort de la region : c'est la valeur absolue qui mesure le drainage.
    accumulation = np.abs(
        accumulation_ds.GetRasterBand(1).ReadAsArray(*window)
    )
    streams_ds = accumulation_ds = None
    if streams is None or accumulation is None:
        raise DelineationError("Lecture impossible autour de l'exutoire.")

    channel = np.isfinite(streams) & (streams > 0)
    if nodata is not None:
        channel &= streams != nodata

    rows, cols = np.nonzero(channel)
    if rows.size:
        xs = origin_x + (col_min + cols + 0.5) * pixel_x
        ys = origin_y + (row_min + rows + 0.5) * pixel_y
        distances = np.hypot(xs - x, ys - y)
        drained = accumulation[rows, cols]
        # Tri par distance, puis par drainage decroissant a distance egale.
        order = np.lexsort((-drained, np.round(distances / abs(pixel_x))))
        pick = order[0]
        chosen = (int(rows[pick]), int(cols[pick]))
        origin = "chevelu"
    else:
        # Aucun chenal a portee : on retombe sur la maille la plus drainee,
        # en signalant que le resultat est fragile.
        flat = int(np.argmax(accumulation))
        chosen = divmod(flat, width)
        origin = "accumulation maximale"

    row, col = chosen
    snapped_x = origin_x + (col_min + col + 0.5) * pixel_x
    snapped_y = origin_y + (row_min + row + 0.5) * pixel_y
    return {
        "x": snapped_x,
        "y": snapped_y,
        "accumulation": float(accumulation[row, col]),
        "shift": math.hypot(snapped_x - x, snapped_y - y),
        "origine": origin,
    }


def delineate(dem_info, outlet, workdir, threshold=STREAM_THRESHOLD,
              snap_radius=SNAP_RADIUS, simplify_cells=SIMPLIFY_CELLS,
              progress=None, feedback=None):
    """Delimite le bassin versant draine par l'exutoire.

    dem_info est le dictionnaire renvoye par core.dem.download_dem.
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
    # Les indicateurs booleens de GRASS ne sont pas transmis : passes a False
    # ils font echouer l'algorithme sans message. Les valeurs par defaut
    # conviennent (ecoulement multiple, ce qui lisse mieux les versants).
    watershed = processing.run(_algorithm("r.watershed"), {
        "elevation": dem_info["path"],
        "threshold": threshold,
        "accumulation": accumulation,
        "drainage": drainage,
        "stream": streams,
        "GRASS_REGION_CELLSIZE_PARAMETER": 0,
    }, feedback=feedback)
    accumulation = watershed["accumulation"]
    drainage = watershed["drainage"]
    streams = watershed["stream"]

    report("Recalage de l'exutoire sur le talweg...")
    snapped = snap_to_thalweg(streams, accumulation, outlet[0], outlet[1],
                              snap_radius)
    x, y = snapped["x"], snapped["y"]
    score = snapped["accumulation"]
    cell_area = cellsize * cellsize
    report("  decale de {0:.1f} m sur le {1} : {2:.0f} mailles drainees, "
           "soit {3:.2f} km2".format(
               snapped["shift"], snapped["origine"], score,
               score * cell_area / 1e6))

    report("Extraction du bassin (r.water.outlet)...")
    basin_raster = processing.run(_algorithm("r.water.outlet"), {
        "input": drainage,
        "coordinates": "{0},{1}".format(x, y),
        "output": os.path.join(workdir, "basin.tif"),
        "GRASS_REGION_CELLSIZE_PARAMETER": 0,
    }, feedback=feedback)["output"]

    report("Vectorisation...")
    polygons = processing.run("gdal:polygonize", {
        "INPUT": basin_raster,
        "BAND": 1,
        "FIELD": "value",
        "EIGHTCONNECTEDNESS": True,
        "OUTPUT": os.path.join(workdir, "basin_raw.gpkg"),
    }, feedback=feedback)["OUTPUT"]

    geometry = _largest_polygon(polygons)
    if geometry is None:
        raise DelineationError(
            "Aucun bassin versant n'a pu etre extrait. L'exutoire est "
            "probablement hors du reseau d'ecoulement."
        )

    area = geometry.area()
    # Le raster d'accumulation annonce combien de mailles se deversent dans
    # l'exutoire : le polygone doit retrouver a peu pres cette surface. Un
    # ecart important signale que le point est tombe a cote du talweg, ce
    # qu'un simple seuil en valeur absolue ne detecte pas - un bassin de
    # 600 m2 est absurde pour une riviere et parfaitement normal pour un
    # fosse.
    expected = score * cell_area
    if expected > 0 and area < 0.5 * expected:
        raise DelineationError(
            "Bassin incoherent : {0:.2f} ha extraits alors que l'exutoire "
            "draine {1:.2f} ha d'apres le modele de terrain.".format(
                area / 1e4, expected / 1e4)
        )
    if area < 20 * cell_area:
        raise DelineationError(
            "Bassin degenere ({0:.0f} m2, {1:.0f} mailles) : l'exutoire n'est "
            "pas tombe sur un talweg. Augmentez le rayon d'accrochage ou "
            "deplacez le point.".format(area, area / cell_area)
        )

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
