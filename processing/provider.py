# -*- coding: utf-8 -*-
"""Fournisseur Processing de BVLIP."""

import os

from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon

from .alg_delineate import DelineateWatershedAlgorithm

ICON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "icons", "icon.png"
)


class BvlipProvider(QgsProcessingProvider):
    """Regroupe les algorithmes du plugin dans la boite a outils."""

    def id(self):
        return "bvlip"

    def name(self):
        return "BVLIP"

    def longName(self):  # noqa: N802 (API QGIS)
        return "BVLIP - Bassins versants"

    def icon(self):
        if os.path.exists(ICON_PATH):
            return QIcon(ICON_PATH)
        return QgsProcessingProvider.icon(self)

    def loadAlgorithms(self):  # noqa: N802
        self.addAlgorithm(DelineateWatershedAlgorithm())
