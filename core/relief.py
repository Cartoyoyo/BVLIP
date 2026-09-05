# -*- coding: utf-8 -*-
"""Relief du bassin, conserve pour les vues en trois dimensions.

Le MNT et les rasters d'ecoulement partent avec le repertoire de travail : ils
pesent de cinquante a trois cents megaoctets et plus rien ne les lit une fois
le bassin delimite. Une vue en relief, elle, a besoin des altitudes - et elle
est demandee apres coup, quand il n'y a plus rien a lire.

On en garde donc juste assez : une grille allegee du seul bassin, quelques
centaines de mailles de cote. A quatre cents mailles sur vingt kilometres, la
maille fait cinquante metres ; c'est sans commune mesure avec le MNT complet -
moins d'un megaoctet contre plusieurs centaines - et amplement suffisant pour
un bloc-diagramme, ou l'oeil ne distingue de toute facon pas la maille.

Rien n'est ecrit sur disque : la grille voyage dans le resultat, comme le
reste. Et tout ce qui sort d'ici est en types Python ordinaires - listes de
couples et tableau numpy - pour que le module des graphiques n'ait a connaitre
ni QGIS ni GDAL.
"""

import numpy as np
from osgeo import gdal

# Cote maximal de la grille conservee, en mailles. Quatre cents suffisent a un
# bloc-diagramme lisible et laissent la rotation a la souris fluide ; au-dela,
# la vue interactive devient poussive sans gagner en lisibilite.
MAX_CELLS = 400

# Marge autour du bassin, en part de sa plus grande dimension. Un bassin pose
# a ras bord d'un bloc-diagramme parait flotter : un peu de terrain autour lui
# rend son assise.
MARGIN_SHARE = 0.04

# Pas d'echantillonnage du reseau hydrographique le long des troncons, en
# metres. Le chevelu n'est ici qu'un trait pose sur le relief : le suivre au
# metre pres n'ajoute rien a l'image et alourdit la rotation.
STREAM_STEP = 60.0


class ReliefError(RuntimeError):
    """Le relief n'a pas pu etre extrait du modele de terrain."""


def _window(dem_info, bbox, max_cells):
    """Fenetre de lecture et taille du tampon, pour l'emprise demandee."""
    xmin, ymin, xmax, ymax = dem_info["bbox"]
    resolution = dem_info["resolution"]
    left = int(max(0, (bbox[0] - xmin) / resolution))
    right = int(min(dem_info["width"], np.ceil((bbox[2] - xmin) / resolution)))
    top = int(max(0, (ymax - bbox[3]) / resolution))
    bottom = int(min(dem_info["height"], np.ceil((ymax - bbox[1]) / resolution)))
    width = max(1, right - left)
    height = max(1, bottom - top)

    # Le tampon garde les proportions : un bassin allonge doit le rester.
    factor = max(width, height) / float(max_cells)
    if factor <= 1.0:
        return (left, top, width, height), width, height
    return (left, top, width, height), max(2, int(width / factor)), \
        max(2, int(height / factor))


def _outline(geometry):
    """Contour exterieur du bassin, en liste de couples."""
    polygon = geometry.asPolygon()
    if not polygon:
        parts = geometry.asMultiPolygon()
        if not parts:
            return []
        polygon = parts[0]
    return [(point.x(), point.y()) for point in polygon[0]]


def _polylines(records, step=STREAM_STEP):
    """Troncons echantillonnes, en listes de couples."""
    lines = []
    for record in records or []:
        geometry = record["geometry"]
        length = geometry.length()
        if length <= 0:
            continue
        count = max(2, int(length / step) + 1)
        line = []
        for index in range(count):
            point = geometry.interpolate(length * index / (count - 1))
            if point.isEmpty():
                continue
            vertex = point.asPoint()
            line.append((vertex.x(), vertex.y()))
        if len(line) > 1:
            lines.append(line)
    return lines


def extract(dem_info, geometry, upstream=None, outlet=None,
            max_cells=MAX_CELLS):
    """Releve le relief du bassin et ce qu'il faut pour le dessiner.

    Renvoie un dictionnaire :
        grid       altitudes (lignes du nord au sud), avec des NaN aux trous
        x, y       coordonnees des centres de maille, en Lambert 93
        contour    ligne de partage des eaux, liste de couples
        reseau     troncons amont echantillonnes, listes de couples
        exutoire   couple, ou None
        maille_m   cote de maille de la grille conservee
    """
    box = geometry.boundingBox()
    margin = MARGIN_SHARE * max(box.width(), box.height())
    bbox = (box.xMinimum() - margin, box.yMinimum() - margin,
            box.xMaximum() + margin, box.yMaximum() + margin)

    dataset = gdal.Open(dem_info["path"])
    if dataset is None:
        raise ReliefError("Modele de terrain illisible : {0}".format(
            dem_info["path"]))
    window, buffer_width, buffer_height = _window(dem_info, bbox, max_cells)
    band = dataset.GetRasterBand(1)
    grid = band.ReadAsArray(*window, buf_xsize=buffer_width,
                            buf_ysize=buffer_height)
    nodata = band.GetNoDataValue()
    dataset = None
    if grid is None:
        raise ReliefError("Lecture impossible du modele de terrain.")

    grid = np.asarray(grid, dtype=np.float32)
    if nodata is not None:
        grid = np.where(grid == nodata, np.nan, grid)
    grid = np.where(np.isfinite(grid), grid, np.nan)

    # Coordonnees des centres de maille du tampon, et non du MNT d'origine :
    # la lecture a rééchantillonne, la maille n'est plus la meme.
    resolution = dem_info["resolution"]
    xmin = dem_info["bbox"][0] + window[0] * resolution
    ymax = dem_info["bbox"][3] - window[1] * resolution
    step_x = window[2] * resolution / buffer_width
    step_y = window[3] * resolution / buffer_height
    x = xmin + (np.arange(buffer_width) + 0.5) * step_x
    y = ymax - (np.arange(buffer_height) + 0.5) * step_y

    return {
        "grid": grid,
        "x": x,
        "y": y,
        "contour": _outline(geometry),
        "reseau": _polylines(upstream),
        "exutoire": tuple(outlet) if outlet else None,
        "maille_m": max(step_x, step_y),
    }
