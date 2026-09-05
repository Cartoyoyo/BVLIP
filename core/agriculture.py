# -*- coding: utf-8 -*-
"""Agriculture declaree du bassin, d'apres les donnees de la PAC.

La source est le Registre parcellaire graphique, c'est-a-dire les parcelles
declarees chaque annee par les exploitants au titre de la politique agricole
commune. C'est la troisieme jambe du meme raisonnement que le bati de la BD
TOPO et le couvert de la BD Foret : Corine Land Cover ne retient rien en
dessous de vingt-cinq hectares, et une mosaique de parcelles agricoles lui
echappe autant qu'un hameau ou qu'un bosquet.

Deux reserves commandent la facon de s'en servir, et le rapport les dit :

  - **le RPG ne couvre que le declare.** Un exploitant qui ne demande pas
    d'aide n'y figure pas, non plus que les terres qui n'ouvrent droit a
    rien. La surface obtenue est un minorant de la surface agricole reelle,
    jamais un inventaire ;
  - **la nomenclature des vingt-huit groupes de culture n'est pas servie**,
    seuls les cent quarante-sept codes detailles le sont, par une table du
    meme service. On s'appuie donc sur ces libelles-la et sur la categorie
    portee par la donnee, plutot que de traduire un code de groupe de
    memoire.

Le numero PACAGE, qui identifie l'exploitation, figure dans certaines couches
du service. Il n'est jamais lu ici : ce module ne rend que des surfaces
agregees, et rien qui puisse designer un exploitant.
"""

import json

from qgis.core import QgsGeometry, QgsJsonUtils

from .geoservices import GeoserviceError, wfs_features, wfs_pages

LAYER_RPG = "RPG.LATEST:parcelles_graphiques"
LAYER_CODES = "RPG.LATEST:codes_cultures"
LAYER_BIO = ("IGNF_RPG_PARCELLES-AGRICOLES-CATEGORISEES_2024:"
             "parcelles_agricole_categorisees_2024")
LAYER_PRAIRIES = "PRAIRIES.SENSIBLES.BCAE:prairies_sensibles"
LAYER_AOC = "AOC-VITICOLES:aire_parcellaire"

# Categorie de culture principale, telle que la donnee la porte. Les libelles
# sont ceux du service lui-meme - sa couche des parcelles categorisees
# s'intitule "terres arables, cultures permanentes, prairies" - et non une
# traduction de notre cru.
CATEGORIES = (
    ("TA", "Terres arables"),
    ("CP", "Cultures permanentes"),
    ("PP", "Prairies permanentes"),
)

# Toute autre valeur - le RPG porte "NA" sur les cultures qui n'entrent dans
# aucune des trois, comme les surfaces temporairement non exploitees - est
# nommee sans qu'on lui prete un sens qu'elle n'a pas.
CATEGORIE_AUTRE = "Catégorie non renseignée"

# Termes du libelle qui designent de l'herbe paturee ou fauchee, par
# opposition a une culture. Ils sont cherches n'importe ou dans le libelle
# servi, et le choix des deux seuls termes n'est pas anodin.
#
# "graminee" avait ete essaye : il attrape "Graminee pure exclusivement pour
# gazon ou pour production de semences certifiees", qui est une culture de
# semences, et surtout "Autre plante fourragere annuelle (ni legumineuse ni
# graminee ni cereale ni oleagineuse)", ou le mot apparait dans une negation.
#
# Le rapprochement sur le debut du libelle avait ete essaye ensuite : il
# manque "Autre prairie temporaire de 5 ans ou moins", et laisse donc les
# prairies temporaires du cote des cultures.
#
# "prairie" et "surface pastorale", cherches partout, rendent exactement cinq
# codes sur les cent quarante-sept - PPH, PTR, SPH, SPL, SIN - sans un seul
# faux positif. Verifie sur la table servie.
#
# Le RPG, lui, range les prairies temporaires en terres arables : les deux
# repartitions du rapport ne se recouvrent donc pas, et la note le dit.
HERBE_TERMES = ("prairie", "surface pastorale")

# Stades de la certification biologique, tels que le RPG les code. "AB" est
# la certification acquise, "C1" a "C3" les trois annees de conversion. Le
# libelle est deduit du code et non invente : le referentiel n'en publie pas
# d'autre, et la lettre parle d'elle-meme.
BIO_STAGES = {
    "AB": "Certifiée agriculture biologique",
    "C1": "En conversion, 1re année",
    "C2": "En conversion, 2e année",
    "C3": "En conversion, 3e année",
}
BIO_CERTIFIE = "AB"

# Palettes de la couche des parcelles, une par nature.
#
# Les verts vont a l'herbe, les tons chauds aux cultures : la carte se lit
# d'abord ainsi, avant meme qu'on aille chercher l'intitule dans la legende.
# A l'interieur de chaque famille les teintes se suivent sans se ressembler,
# et la liste tourne si les cultures sont plus nombreuses qu'elle.
COULEURS_HERBE = ("#4f9d69", "#7fbf8c", "#2f7d4f", "#a3c4a8", "#5aa87a")
COULEURS_CULTURE = (
    "#c9954f", "#b5705f", "#d4b06a", "#a8724a", "#8a6ea8",
    "#c98f8f", "#9a8c5a", "#b58fc4", "#7a8fa8", "#c4a86a",
)

# Nombre de cultures detaillees rendues. Au-dela, la queue de distribution
# n'apprend plus rien : sur un bassin d'elevage, trois codes font neuf
# dixiemes de la surface.
MAX_CULTURES = 12

# Table des codes culture, chargee une fois par session. Cent quarante-sept
# lignes sans geometrie : elle ne merite pas d'etre rapatriee a chaque bassin.
_CODES = None


class AgricultureError(RuntimeError):
    """L'agriculture declaree n'a pas pu etre etablie."""


def culture_labels(timeout=60):
    """Libelles des codes culture, tels que le service les publie."""
    global _CODES
    if _CODES is None:
        table = {}
        for feature in wfs_features(LAYER_CODES, timeout=timeout):
            properties = feature.get("properties") or {}
            code = properties.get("code")
            if code:
                table[str(code)] = properties.get("libelle") or str(code)
        _CODES = table
    return _CODES


def _sans_accent(text):
    import unicodedata
    decomposed = unicodedata.normalize("NFD", str(text or ""))
    return "".join(c for c in decomposed
                   if unicodedata.category(c) != "Mn").lower()


def _is_grass(code, label, categorie):
    """Cette culture est-elle de l'herbe plutot qu'une culture ?

    Le libelle servi tranche quand on l'a ; a defaut - table des codes
    indisponible - on retombe sur la categorie portee par la donnee, qui ne
    connait que les prairies permanentes.
    """
    if label:
        plat = _sans_accent(label)
        return any(terme in plat for terme in HERBE_TERMES)
    return categorie == "PP"


def _geometry(feature):
    return QgsGeometry(
        QgsJsonUtils.geometryFromGeoJson(json.dumps(feature["geometry"]))
    )


def _clipped(feature, basin):
    geometry = _geometry(feature)
    if geometry.isEmpty():
        return 0.0
    clipped = geometry.intersection(basin)
    return 0.0 if clipped.isEmpty() else clipped.area()


def _bbox(basin):
    box = basin.boundingBox()
    return (box.xMinimum(), box.yMinimum(), box.xMaximum(), box.yMaximum())


def _shares(totals, labels, total_area, limit=None, default=None):
    """Repartition triee, en hectares et en part du bassin.

    default nomme les codes absents de la table plutot que de les afficher
    bruts : un "NA" seul dans une colonne de libelles n'apprend rien.
    """
    ranked = sorted(totals.items(), key=lambda kv: -kv[1])
    if limit:
        ranked = ranked[:limit]
    return [
        {
            "code": code,
            "libelle": labels.get(code) or default or code,
            "surface_ha": area / 1e4,
            "part_pct": 100.0 * area / total_area if total_area else None,
        }
        for code, area in ranked if area > 0
    ]


def declared_parcels(basin, progress=None, timeout=120):
    """Parcelles declarees a la PAC recoupant le bassin."""
    if progress:
        progress("Parcelles PAC (RPG)...")
    total = basin.area()
    if total <= 0:
        raise AgricultureError("Bassin de surface nulle.")

    labels = {}
    try:
        labels = culture_labels()
    except GeoserviceError:
        # Sans la table, les codes restent bruts : mieux vaut un "PPH" qu'un
        # libelle invente, et la repartition garde tout son sens.
        labels = {}

    par_culture = {}
    par_categorie = {}
    surfaces = []
    herbe = 0.0
    cultures_area = 0.0
    # Les parcelles sont conservees avec leur forme : elles alimentent la
    # couche QGIS. Elles se comptent en centaines sur un bassin moyen, en
    # milliers sur un grand - du meme ordre que le chevelu, deja garde.
    parcelles = []
    for page in wfs_pages(LAYER_RPG, bbox=_bbox(basin), timeout=timeout):
        for feature in page:
            area = _clipped(feature, basin)
            if area <= 0:
                continue
            properties = feature["properties"]
            culture = str(properties.get("code_cultu") or "").strip()
            categorie = str(properties.get("cat_cult_p") or "").strip()
            clipped = _geometry(feature).intersection(basin)
            par_culture[culture] = par_culture.get(culture, 0.0) + area
            par_categorie[categorie] = par_categorie.get(categorie, 0.0) + area
            est_herbe = _is_grass(culture, labels.get(culture), categorie)
            if est_herbe:
                herbe += area
            else:
                cultures_area += area
            surfaces.append(area)
            parcelles.append({
                "code": culture,
                "libelle": labels.get(culture) or culture,
                "categorie": dict(CATEGORIES).get(categorie,
                                                  CATEGORIE_AUTRE),
                "herbe": est_herbe,
                "surface_ha": area / 1e4,
                "part_pct": 100.0 * area / total,
                "geometrie": clipped,
            })
        del page

    if not surfaces:
        return {
            "surface_ha": 0.0, "part_pct": 0.0, "nb_parcelles": 0,
            "taille_moyenne_ha": None, "taille_mediane_ha": None,
            "categories": [], "cultures": [], "dominante": None,
            "dominante_pct": None,
            "herbe_ha": None, "herbe_pct": None, "herbe_part_declare": None,
            "cultures_ha": None, "cultures_pct": None,
            "cultures_part_declare": None, "parcelles": [],
            "source": "RPG — Registre parcellaire graphique (IGN / ASP)",
        }

    declaree = sum(surfaces)
    surfaces.sort()
    milieu = len(surfaces) // 2
    mediane = (surfaces[milieu] if len(surfaces) % 2
               else (surfaces[milieu - 1] + surfaces[milieu]) / 2.0)

    categories = _shares(par_categorie, dict(CATEGORIES), total,
                         default=CATEGORIE_AUTRE)
    cultures = _shares(par_culture, labels, total, MAX_CULTURES,
                       default="Code non répertorié")
    return {
        "surface_ha": declaree / 1e4,
        "part_pct": 100.0 * declaree / total,
        "nb_parcelles": len(surfaces),
        "taille_moyenne_ha": declaree / len(surfaces) / 1e4,
        "taille_mediane_ha": mediane / 1e4,
        # L'herbe et les cultures, la distinction que reclame la lecture d'un
        # bassin : ce qui est paturé ou fauche d'un cote, ce qui est laboure
        # de l'autre. Les parts sont donnees deux fois, sur le bassin et sur
        # le seul declare, parce que les deux questions se posent.
        "herbe_ha": herbe / 1e4,
        "herbe_pct": 100.0 * herbe / total,
        "herbe_part_declare": 100.0 * herbe / declaree if declaree else None,
        "cultures_ha": cultures_area / 1e4,
        "cultures_pct": 100.0 * cultures_area / total,
        "cultures_part_declare": (100.0 * cultures_area / declaree
                                  if declaree else None),
        "categories": categories,
        "cultures": cultures,
        "parcelles": parcelles,
        "dominante": cultures[0]["libelle"] if cultures else None,
        "dominante_pct": cultures[0]["part_pct"] if cultures else None,
        "source": "RPG — Registre parcellaire graphique (IGN / ASP)",
    }


def organic_parcels(basin, progress=None, timeout=120):
    """Parcelles declarees en agriculture biologique ou en conversion.

    La couche interrogee n'est pas celle des parcelles anonymes : c'est la
    couche categorisee, seule a porter les champs "bio" et "cond_bio". Elle
    porte aussi le numero PACAGE, qui identifie l'exploitation - il n'est pas
    lu, et n'entre ni dans les statistiques ni dans la couche produite.

    Les MAEC, elles, ne sont pas publiees a la parcelle : l'engagement est une
    donnee d'aide individuelle, et aucun des trente attributs de cette couche
    ne le porte. Le bio est ce qui s'en approche le plus dans l'ouvert.
    """
    if progress:
        progress("Agriculture biologique...")
    total = basin.area()
    if total <= 0:
        raise AgricultureError("Bassin de surface nulle.")

    labels = {}
    try:
        labels = culture_labels()
    except GeoserviceError:
        labels = {}

    certifie = 0.0
    conversion = 0.0
    declare = 0.0
    parcelles = []
    for page in wfs_pages(LAYER_BIO, bbox=_bbox(basin), timeout=timeout):
        for feature in page:
            properties = feature["properties"]
            area = _clipped(feature, basin)
            if area <= 0:
                continue
            declare += area
            if not properties.get("bio"):
                continue
            stade = str(properties.get("cond_bio") or "").strip().upper()
            if stade == BIO_CERTIFIE:
                certifie += area
            else:
                conversion += area
            culture = str(properties.get("code_cultu") or "").strip()
            parcelles.append({
                "statut": ("Certifiée AB" if stade == BIO_CERTIFIE
                           else "En conversion"),
                "stade": BIO_STAGES.get(stade, stade or "Non précisé"),
                "culture": labels.get(culture) or culture,
                "surface_ha": area / 1e4,
                "part_pct": 100.0 * area / total,
                "geometrie": _geometry(feature).intersection(basin),
            })
        del page

    engage = certifie + conversion
    return {
        "certifie_ha": certifie / 1e4,
        "certifie_pct": 100.0 * certifie / total,
        "conversion_ha": conversion / 1e4,
        "conversion_pct": 100.0 * conversion / total,
        "engage_ha": engage / 1e4,
        "engage_pct": 100.0 * engage / total,
        # Part du declare, et non du bassin : c'est la question que pose un
        # lecteur agricole, et elle n'a pas la meme reponse.
        "part_declare": 100.0 * engage / declare if declare else None,
        "nb_parcelles": len(parcelles),
        "parcelles": parcelles,
        "source": "RPG parcelles catégorisées (IGN / ASP)",
    }


def _simple_area(typename, basin, label, progress=None, timeout=90):
    """Surface cumulee d'une couche surfacique, et nombre d'entites."""
    if progress:
        progress(label + "...")
    total = basin.area()
    area = 0.0
    count = 0
    for page in wfs_pages(typename, bbox=_bbox(basin), timeout=timeout):
        for feature in page:
            clipped = _clipped(feature, basin)
            if clipped > 0:
                area += clipped
                count += 1
        del page
    return {
        "surface_ha": area / 1e4,
        "part_pct": 100.0 * area / total if total else None,
        "nb": count,
    }


def palette(labels_herbe, labels_culture):
    """Une teinte par intitule, verte pour l'herbe et chaude pour le reste.

    Les intitules sont pris dans l'ordre ou l'appelant les donne - decroissant
    par surface - pour que les cultures les plus etendues recoivent les
    teintes les plus tranchees de leur famille.
    """
    couleurs = {}
    for index, libelle in enumerate(labels_herbe):
        couleurs[libelle] = COULEURS_HERBE[index % len(COULEURS_HERBE)]
    for index, libelle in enumerate(labels_culture):
        couleurs[libelle] = COULEURS_CULTURE[index % len(COULEURS_CULTURE)]
    return couleurs


def compute(basin, with_rpg=True, with_bio=True, with_prairies=True,
            with_aoc=True, progress=None):
    """Agriculture declaree du bassin.

    Une couche indisponible laisse sa partie a None sans emporter les autres :
    le RPG est le gros morceau, les deux autres ne sont que des complements.
    """
    values = {"rpg": None, "bio": None, "prairies": None, "aoc": None,
              "erreurs": []}
    if with_rpg:
        try:
            values["rpg"] = declared_parcels(basin, progress)
        except (GeoserviceError, AgricultureError) as exc:
            values["erreurs"].append("Parcelles PAC : {0}".format(exc))
    if with_bio:
        try:
            values["bio"] = organic_parcels(basin, progress)
        except (GeoserviceError, AgricultureError) as exc:
            values["erreurs"].append("Agriculture biologique : {0}".format(exc))
    if with_prairies:
        try:
            values["prairies"] = _simple_area(
                LAYER_PRAIRIES, basin, "Prairies sensibles", progress)
        except GeoserviceError as exc:
            values["erreurs"].append("Prairies sensibles : {0}".format(exc))
    if with_aoc:
        try:
            values["aoc"] = _simple_area(
                LAYER_AOC, basin, "Aires AOC viticoles", progress)
        except GeoserviceError as exc:
            values["erreurs"].append("Aires AOC : {0}".format(exc))
    return values
