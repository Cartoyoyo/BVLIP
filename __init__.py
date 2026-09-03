# -*- coding: utf-8 -*-
"""BVLIP - Bassin Versant en amont d'un point.

Point d'entree QGIS : ne contient que la fabrique de classe, pour que le
chargement du plugin reste instantane et sans effet de bord.
"""


def classFactory(iface):  # noqa: N802 (nom impose par QGIS)
    from .plugin_main import BvlipPlugin
    return BvlipPlugin(iface)
