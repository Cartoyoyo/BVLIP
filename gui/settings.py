# -*- coding: utf-8 -*-
"""Reglages du plugin, conserves d'une session a l'autre.

Ils vivent dans les preferences de QGIS plutot que dans le panneau : un rayon
d'accrochage ou un choix de langue n'a pas a etre repose a chaque ouverture,
et sortir ces reglages du panneau libere la place pour ce qui sert a chaque
usage, le choix de l'exutoire et le lancement.
"""

from qgis.PyQt.QtCore import QSettings

PREFIX = "BVLIP/"

# (cle, valeur par defaut, type). Le type sert a relire correctement : QSettings
# rend des chaines sous Windows, et "false" est une chaine vraie en Python.
DEFAULTS = (
    ("snap_radius", 50, int),
    ("thalweg_radius", 50, int),
    ("with_metrics", True, bool),
    ("with_land_cover", True, bool),
    ("refine", False, bool),
    ("language", "", str),
)


DEFAULTS_BY_KEY = {key: default for key, default, _kind in DEFAULTS}


def _cast(value, default, kind):
    if value is None:
        return default
    if kind is bool:
        if isinstance(value, bool):
            return value
        return str(value).lower() in ("true", "1", "yes")
    try:
        return kind(value)
    except (TypeError, ValueError):
        return default


def load():
    """Renvoie tous les reglages, valeurs par defaut comprises."""
    store = QSettings()
    values = {}
    for key, default, kind in DEFAULTS:
        values[key] = _cast(store.value(PREFIX + key), default, kind)
    return values


def save(values):
    """Enregistre les reglages fournis ; les autres restent inchanges."""
    store = QSettings()
    known = {key for key, _default, _kind in DEFAULTS}
    for key, value in values.items():
        if key in known:
            store.setValue(PREFIX + key, value)


def reset():
    """Efface les reglages, ramenant tout aux valeurs par defaut."""
    store = QSettings()
    for key, _default, _kind in DEFAULTS:
        store.remove(PREFIX + key)


def pipeline_options(values=None, **overrides):
    """Construit les options de traitement a partir des reglages."""
    from ..core.pipeline import PipelineOptions

    values = values or load()
    options = PipelineOptions(
        snap_radius=float(values["snap_radius"]),
        thalweg_radius=float(values["thalweg_radius"]),
        with_metrics=values["with_metrics"],
        with_land_cover=values["with_land_cover"],
        refine=values["refine"],
    )
    for key, value in overrides.items():
        setattr(options, key, value)
    return options
