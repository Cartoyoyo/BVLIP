# -*- coding: utf-8 -*-
"""Reglages du plugin, conserves d'une session a l'autre.

Ils vivent dans les preferences de QGIS plutot que dans le panneau : un rayon
d'accrochage ou un choix de langue n'a pas a etre repose a chaque ouverture,
et sortir ces reglages du panneau libere la place pour ce qui sert a chaque
usage, le choix de l'exutoire et le lancement.

Le choix des donnees a rapatrier fait exception : il se retouche d'un bassin
a l'autre, il reste donc dans le panneau. Il y est conserve tout de meme, sous
la forme d'une seule chaine de cles separees par des virgules - voir
core.datasets, qui la fabrique et la relit.
"""

from qgis.PyQt.QtCore import QSettings

from ..core import datasets as catalogue

PREFIX = "BVLIP/"

# (cle, valeur par defaut, type). Le type sert a relire correctement : QSettings
# rend des chaines sous Windows, et "false" est une chaine vraie en Python.
#
# La valeur par defaut de "datasets" est None et non la liste des defauts :
# None dit "aucun reglage conserve", et se distingue ainsi de la chaine vide,
# qui est une selection vide voulue par l'utilisateur.
DEFAULTS = (
    ("snap_radius", 50, int),
    ("thalweg_radius", 50, int),
    ("datasets", None, str),
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


def selected_datasets(values=None):
    """Ensemble des donnees choisies, tel qu'il a ete conserve."""
    values = values or load()
    return catalogue.from_setting(values.get("datasets"))


def save_datasets(selection):
    """Conserve la selection de donnees."""
    save({"datasets": catalogue.to_setting(selection)})


def pipeline_options(values=None, **overrides):
    """Construit les options de traitement a partir des reglages."""
    from ..core.pipeline import PipelineOptions

    values = values or load()
    options = PipelineOptions(
        snap_radius=float(values["snap_radius"]),
        thalweg_radius=float(values["thalweg_radius"]),
        datasets=selected_datasets(values),
    )
    for key, value in overrides.items():
        setattr(options, key, value)
    return options
