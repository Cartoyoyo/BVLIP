# -*- coding: utf-8 -*-
"""Catalogue de ce que le traitement peut rapatrier, et de ce qu'il calcule.

Une seule table decrit tout : le panneau en tire ses onglets et ses cases,
les reglages ce qu'ils conservent d'une session a l'autre, l'algorithme
Processing sa liste a choix multiple, et le pipeline ce qu'il doit executer.
Ajouter une donnee se fait ici et nulle part ailleurs - a charge d'ecrire son
libelle dans i18n et de la brancher dans pipeline.

Le module ne depend pas de QGIS. C'est voulu : les outils de controle le
lisent hors de son environnement, comme ils lisent deja la table des champs.

Les cles d'onglet et de donnee commandent leurs cles de traduction, par
prefixe : l'onglet "eau" se nomme par "dstab_eau", la donnee "roe" par
"ds_roe" et se decrit par "dsinfo_roe". Cette regle est verifiee par
tools/check_i18n, qui saurait sinon signaler ces cles comme jamais
utilisees - elles ne sont pas ecrites en toutes lettres dans un appel a tr().
"""

# (cle, ordre d'apparition). Cinq onglets, et pas un de plus : au-dela, les
# etiquettes ne tiennent plus dans la largeur d'un panneau lateral.
TABS = ("bassin", "sol", "agricole", "zonages", "eau")

# (cle, onglet, coche par defaut)
#
# Les deux premieres ne telechargent rien - elles decident d'un calcul - mais
# elles se choisissent au meme endroit que le reste : ce que l'utilisateur
# veut, c'est une seule liste de ce qu'il aura dans sa table, sans avoir a
# savoir ce qui vient du reseau et ce qui vient du MNT.
#
# L'affinage est seul a ne pas etre coche : il double la duree du calcul et
# ne change pas la surface. Tout le reste est coche, pour qu'un premier
# lancement rende un bassin complet sans avoir rien a regler.
DATASETS = (
    ("metriques", "bassin", True),
    ("affinage", "bassin", False),

    ("corine", "sol", True),
    ("bati", "sol", True),
    ("foret", "sol", True),

    ("rpg", "agricole", True),
    ("bio", "agricole", True),
    ("prairies", "agricole", True),
    ("aoc", "agricole", True),

    ("znieff1", "zonages", True),
    ("znieff2", "zonages", True),
    ("zsc", "zonages", True),
    ("zps", "zonages", True),
    ("apb", "zonages", True),
    ("rnn", "zonages", True),
    ("rnr", "zonages", True),
    ("pnr", "zonages", True),
    ("ramsar", "zonages", True),
    ("zhumide", "zonages", True),
    ("nitrate", "zonages", True),
    ("eutroph", "zonages", True),

    ("masse_eau", "eau", True),
    ("meso", "eau", True),
    ("her", "eau", True),
    ("roe", "eau", True),
    ("hydrometrie", "eau", True),
    ("steu", "eau", True),
    ("population", "eau", True),
    ("prelevements", "eau", True),
)

KEYS = tuple(key for key, _tab, _on in DATASETS)
DEFAULTS = frozenset(key for key, _tab, on in DATASETS if on)

# Cles de l'onglet des zonages : ce sont exactement celles de
# protected.ZONAGES, et le controle ci-dessous s'assure qu'elles ne divergent
# pas. protected n'est pas importe ici - il tirerait QGIS avec lui - donc la
# verification vit dans tools/check_fields, qui a le droit de lire les deux.
ZONAGE_KEYS = tuple(key for key, tab, _on in DATASETS if tab == "zonages")


def keys_of(tab):
    """Cles d'un onglet, dans l'ordre de la table."""
    return tuple(key for key, group, _on in DATASETS if group == tab)


def tab_label_key(tab):
    return "dstab_" + tab


def label_key(key):
    return "ds_" + key


def info_key(key):
    """Cle de la description longue, celle qui s'affiche au survol du i."""
    return "dsinfo_" + key


def normalise(selection):
    """Ramene une selection quelconque a un ensemble de cles connues.

    None vaut "tout ce qui est coche par defaut" : c'est ce que recoit un
    appelant qui ne se preoccupe pas du detail, l'algorithme Processing lance
    sans parametre ou un appel direct au pipeline depuis un script.
    """
    if selection is None:
        return set(DEFAULTS)
    known = set(KEYS)
    return {str(key) for key in selection if str(key) in known}


def to_setting(selection):
    """Serialise une selection pour QSettings, dans l'ordre de la table.

    L'ordre est celui de la table et non celui de l'ensemble : une valeur
    conservee doit se relire a l'identique d'une session a l'autre, et un
    ensemble Python ne garantit pas son ordre entre deux executions.
    """
    chosen = normalise(selection)
    return ",".join(key for key in KEYS if key in chosen)


def from_setting(text):
    """Relit une selection conservee. Une valeur absente rend les defauts.

    La chaine vide est une selection vide legitime - l'utilisateur a tout
    decoche - et se distingue donc de None, qui est l'absence de reglage.
    """
    if text is None:
        return set(DEFAULTS)
    return normalise(str(text).split(","))
