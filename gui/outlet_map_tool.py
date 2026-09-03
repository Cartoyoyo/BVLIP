# -*- coding: utf-8 -*-
"""Outil de carte pour designer l'exutoire du bassin versant.

Le point clique est immediatement reprojete en Lambert 93 (EPSG:2154) : tout
le reste de la chaine de traitement raisonne dans ce systeme, qui est celui
du RGE ALTI et de la BD TOPO.
"""

from qgis.core import (
    QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsPointXY,
    QgsProject,
)
from qgis.gui import QgsMapTool, QgsVertexMarker
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QColor

LAMBERT93 = "EPSG:2154"


class OutletMarker(QgsVertexMarker):
    """Repere de l'exutoire sur le canevas.

    C'est une classe a part entiere, et non un QgsVertexMarker nu, pour qu'on
    puisse retrouver nos propres reperes parmi les objets du canevas et les
    retirer sans toucher a ceux des autres extensions.
    """


class OutletMapTool(QgsMapTool):
    """Emet les coordonnees Lambert 93 du point clique et l'affiche sur la carte."""

    outlet_picked = pyqtSignal(float, float)

    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas = canvas
        self.setCursor(Qt.CursorShape.CrossCursor)
        self._marker = None
        # Un rechargement du plugin cree un nouvel outil sans que l'ancien ait
        # eu l'occasion de retirer son repere : le canevas en garde la
        # propriete et les points s'accumulent a l'ecran. On fait le menage a
        # la construction, ce qui couvre aussi les fermetures brutales.
        self.clear_strays()

    def clear_strays(self):
        """Retire du canevas les reperes d'exutoire laisses par une session
        precedente."""
        scene = self.canvas.scene()
        if scene is None:
            return
        for item in list(scene.items()):
            if isinstance(item, OutletMarker):
                scene.removeItem(item)
        self._marker = None

    def canvasReleaseEvent(self, event):  # noqa: N802 (API Qt)
        point = self.toMapCoordinates(event.pos())
        transformed = self._to_lambert93(point)
        if transformed is None:
            return
        self.show_marker(point)
        self.outlet_picked.emit(transformed.x(), transformed.y())

    def _to_lambert93(self, point):
        """Reprojette depuis le SCR du canevas ; renvoie None si la transformation echoue."""
        source = self.canvas.mapSettings().destinationCrs()
        target = QgsCoordinateReferenceSystem(LAMBERT93)
        if source == target:
            return QgsPointXY(point)
        transform = QgsCoordinateTransform(source, target, QgsProject.instance())
        try:
            return transform.transform(point)
        except Exception:  # hors zone Lambert 93, ou SCR du projet non defini
            return None

    def show_marker(self, map_point):
        """Place (ou deplace) le reperage visuel de l'exutoire sur le canevas."""
        if self._marker is None:
            self._marker = OutletMarker(self.canvas)
            self._marker.setIconType(QgsVertexMarker.IconType.ICON_CIRCLE)
            self._marker.setColor(QColor(192, 57, 43))
            self._marker.setFillColor(QColor(231, 76, 60, 160))
            self._marker.setIconSize(14)
            self._marker.setPenWidth(3)
        self._marker.setCenter(QgsPointXY(map_point))
        self._marker.show()

    def clear_marker(self):
        """Retire le repere courant, et tout repere oublie en chemin."""
        self.clear_strays()

    def deactivate(self):
        super().deactivate()
        self.deactivated.emit()
