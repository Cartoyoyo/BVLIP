# -*- coding: utf-8 -*-
"""Decoupe en serie d'entites sur le contour du bassin.

Les couches denses - haies, habitats CarHab - se comptent en dizaines de
milliers d'entites par bassin. Les intersecter une a une avec le contour,
qui porte lui-meme des milliers de sommets, coute une operation GEOS
complete par entite, meme pour celles qui tombent entierement dedans ou
entierement dehors, c'est-a-dire presque toutes.

Le contour est donc prepare une fois : le test d'appartenance devient
quasi gratuit, et seule la frange d'entites a cheval sur la limite paie
encore une intersection.
"""

import json

from qgis.core import QgsGeometry, QgsJsonUtils


def geometry_of(feature):
    """Geometrie d'une entite GeoJSON, vide si elle n'en porte pas."""
    shape = feature.get("geometry")
    if not shape:
        return QgsGeometry()
    return QgsGeometry(QgsJsonUtils.geometryFromGeoJson(json.dumps(shape)))


class PreparedBasin:
    """Le bassin, prepare pour des milliers de decoupes successives.

    A n'utiliser que dans le fil qui l'a cree : le moteur prepare de GEOS
    n'est pas partage entre fils.
    """

    def __init__(self, basin):
        self.basin = basin
        self.area = basin.area()
        self._engine = QgsGeometry.createGeometryEngine(basin.constGet())
        self._engine.prepareGeometry()

    def clip(self, geometry):
        """La part de la geometrie comprise dans le bassin, ou None."""
        if geometry is None or geometry.isEmpty():
            return None
        shape = geometry.constGet()
        if not self._engine.intersects(shape):
            return None
        if self._engine.contains(shape):
            return geometry
        clipped = geometry.intersection(self.basin)
        return None if clipped.isEmpty() else clipped
