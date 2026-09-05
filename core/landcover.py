# -*- coding: utf-8 -*-
"""Occupation du sol du bassin versant.

Trois sources, complementaires plutot que concurrentes :

  Corine Land Cover 2018   couverture complete et nomenclature normalisee, mais
                           unite minimale de collecte de 25 ha. Sur un petit
                           bassin, elle donne la structure d'ensemble et rien
                           de plus.
  BD TOPO                  batiments et zones d'habitation, au metre pres.
                           Indispensable ici : CLC efface purement et
                           simplement les hameaux, et annoncerait 0 % d'urbain
                           sur un bassin qui en compte plusieurs.
  BD Foret v2              formations vegetales forestieres, a 0,5 ha. Meme
                           defaut corrige que pour le bati, du cote de la
                           foret cette fois : CLC ne voit pas un boisement de
                           dix hectares, la ou il change l'ecoulement.

Les trois ne sont pas additionnees. CLC fournit la repartition, qui somme a
100 %, la BD TOPO un indicateur de bati et la BD Foret un indicateur de
boisement, tous deux mesures independamment. Les melanger reviendrait a
compter deux fois les memes surfaces.
"""

import json

from qgis.core import QgsGeometry, QgsJsonUtils

from .geoservices import GeoserviceError, wfs_pages

LAYER_CLC = "LANDCOVER.CLC18_FR:clc18_fr"
LAYER_BUILDINGS = "BDTOPO_V3:batiment"
LAYER_SETTLEMENTS = "BDTOPO_V3:zone_d_habitation"
LAYER_FOREST = "LANDCOVER.FORESTINVENTORY.V2:formation_vegetale"

# Regroupement des formations de la BD Foret v2 en trois grands peuplements.
#
# La lecture se fait sur le libelle du regroupement en onze classes - "Foret
# fermee feuillus", "Foret ouverte coniferes" - et non sur l'attribut
# d'essence. Celui-ci descend jusqu'a l'espece : sur un bassin de la Montagne
# bourbonnaise il rend Douglas, Hetre, Melese, Sapin-epicea, Chenes decidus,
# la ou seuls "Feuillus", "Coniferes" et "Mixte" etaient attendus. Trier sur
# lui reviendrait a ne compter que les polygones les moins renseignes, et a
# sous-estimer le boisement d'un facteur deux.
FOREST_GROUPS = (
    ("feuillus", "feuillus"),
    ("coniferes", "conifères"),
    ("mixte", "mixte"),
)

# Nomenclature Corine Land Cover, niveau 3. Les libelles sont ceux du
# referentiel europeen traduit, conserves tels quels pour que le rapport soit
# comparable a n'importe quelle autre etude CLC.
CLC_LABELS = {
    "111": "Tissu urbain continu",
    "112": "Tissu urbain discontinu",
    "121": "Zones industrielles ou commerciales",
    "122": "Reseaux routier et ferroviaire",
    "123": "Zones portuaires",
    "124": "Aeroports",
    "131": "Extraction de materiaux",
    "132": "Decharges",
    "133": "Chantiers",
    "141": "Espaces verts urbains",
    "142": "Equipements sportifs et de loisirs",
    "211": "Terres arables hors perimetres d'irrigation",
    "212": "Perimetres irrigues en permanence",
    "213": "Rizieres",
    "221": "Vignobles",
    "222": "Vergers et petits fruits",
    "223": "Oliveraies",
    "231": "Prairies",
    "241": "Cultures annuelles associees aux cultures permanentes",
    "242": "Systemes culturaux et parcellaires complexes",
    "243": "Surfaces agricoles interrompues par des espaces naturels",
    "244": "Territoires agroforestiers",
    "311": "Forets de feuillus",
    "312": "Forets de coniferes",
    "313": "Forets melangees",
    "321": "Pelouses et paturages naturels",
    "322": "Landes et broussailles",
    "323": "Vegetation sclerophylle",
    "324": "Foret et vegetation arbustive en mutation",
    "331": "Plages, dunes et sable",
    "332": "Roches nues",
    "333": "Vegetation clairsemee",
    "334": "Zones incendiees",
    "335": "Glaciers et neiges eternelles",
    "411": "Marais interieurs",
    "412": "Tourbieres",
    "421": "Marais maritimes",
    "422": "Marais salants",
    "423": "Zones intertidales",
    "511": "Cours et voies d'eau",
    "512": "Plans d'eau",
    "521": "Lagunes littorales",
    "522": "Estuaires",
    "523": "Mers et oceans",
}

CLC_LEVEL1 = {
    "1": "Territoires artificialises",
    "2": "Territoires agricoles",
    "3": "Forets et milieux semi-naturels",
    "4": "Zones humides",
    "5": "Surfaces en eau",
}


# Teintes des formations de la BD Foret, reconnues au mot qui les distingue
# dans leur libelle. L'ordre compte : "sans couvert arbore" ne doit rencontrer
# aucun mot avant de tomber sur la teinte par defaut.
#
# Les libelles de l'inventaire ne contiennent aucune negation - "Foret fermee
# feuillus", "Lande", "Formation herbacee" - le rapprochement au mot y est
# donc sans piege, a la difference des codes culture du RPG.
FOREST_COLORS = (
    ("feuillus", "#4f9d69"),
    ("conifères", "#2f6d5a"),
    ("mixte", "#7a9d4f"),
    ("peupleraie", "#8fbf9d"),
    ("lande", "#b5a05f"),
    ("herbacée", "#c4c48a"),
)
FOREST_DEFAULT = "#9aa89a"


def formation_color(libelle):
    """Teinte d'une formation vegetale, d'apres son libelle."""
    plat = (libelle or "").lower()
    for mot, couleur in FOREST_COLORS:
        if mot in plat:
            return couleur
    return FOREST_DEFAULT


class LandCoverError(RuntimeError):
    """L'occupation du sol n'a pas pu etre etablie."""


def _accumulate(typename, bbox, basin, timeout=90):
    """Cumule la surface d'intersection avec le bassin, page par page.

    Les entites sont traitees puis jetees au fur et a mesure. Sur un bassin de
    plusieurs centaines de kilometres carres, le bati de la BD TOPO se compte
    en dizaines de milliers de polygones : les garder tous en memoire pour
    n'en tirer qu'une somme serait du gaspillage pur, et sur un poste a
    l'etroit cela suffit a faire echouer le traitement.

    Renvoie (surface cumulee en m2, nombre d'entites retenues).
    """
    area = 0.0
    count = 0
    for page in wfs_pages(typename, bbox=bbox, timeout=timeout):
        for feature in page:
            clipped = _clipped_area(feature, basin)
            if clipped > 0:
                area += clipped
                count += 1
        del page
    return area, count


def _clipped_area(feature, basin):
    geometry = QgsGeometry(
        QgsJsonUtils.geometryFromGeoJson(json.dumps(feature["geometry"]))
    )
    if geometry.isEmpty():
        return 0.0
    clipped = geometry.intersection(basin)
    return 0.0 if clipped.isEmpty() else clipped.area()


def _bbox(basin):
    box = basin.boundingBox()
    return (box.xMinimum(), box.yMinimum(), box.xMaximum(), box.yMaximum())


def corine(basin, progress=None):
    """Repartition Corine Land Cover 2018 sur le bassin.

    Renvoie les classes de niveau 3 et l'agregation de niveau 1, chacune avec
    surface et part, plus le taux de couverture effectivement atteint.
    """
    if progress:
        progress("Corine Land Cover 2018...")
    total = basin.area()
    if total <= 0:
        raise LandCoverError("Bassin de surface nulle.")

    # Seule la repartition par code est conservee : les polygones sont
    # cumules puis oublies page apres page.
    by_code = {}
    for page in wfs_pages(LAYER_CLC, bbox=_bbox(basin), timeout=90):
        for feature in page:
            area = _clipped_area(feature, basin)
            if area <= 0:
                continue
            code = str(feature["properties"].get("code_18") or "").strip()
            by_code[code] = by_code.get(code, 0.0) + area
        del page

    covered = sum(by_code.values())
    classes = [
        {
            "code": code,
            "libelle": CLC_LABELS.get(code, "Classe {0}".format(code)),
            "surface_ha": area / 1e4,
            "part_pct": 100.0 * area / total,
        }
        for code, area in sorted(by_code.items(), key=lambda kv: -kv[1])
    ]

    by_level1 = {}
    for code, area in by_code.items():
        by_level1[code[:1]] = by_level1.get(code[:1], 0.0) + area
    groups = [
        {
            "code": code,
            "libelle": CLC_LEVEL1.get(code, "Niveau {0}".format(code)),
            "surface_ha": area / 1e4,
            "part_pct": 100.0 * area / total,
        }
        for code, area in sorted(by_level1.items(), key=lambda kv: -kv[1])
    ]

    return {
        "classes": classes,
        "niveaux1": groups,
        "couverture_pct": 100.0 * covered / total,
        "source": "Corine Land Cover 2018 (unite minimale 25 ha)",
    }


def built_up(basin, progress=None):
    """Emprise batie mesuree sur la BD TOPO.

    Deux indicateurs distincts : l'emprise au sol des batiments, qui approche
    la surface reellement impermeabilisee, et les zones d'habitation, qui
    delimitent les hameaux avec leurs abords.
    """
    if progress:
        progress("Bati BD TOPO...")
    total = basin.area()
    bbox = _bbox(basin)
    result = {}

    for key, typename in (("batiment", LAYER_BUILDINGS),
                          ("zone_habitation", LAYER_SETTLEMENTS)):
        try:
            area, count = _accumulate(typename, bbox, basin)
        except GeoserviceError:
            result[key + "_ha"] = None
            result[key + "_pct"] = None
            result[key + "_nb"] = None
            continue
        result[key + "_ha"] = area / 1e4
        result[key + "_pct"] = 100.0 * area / total if total else None
        result[key + "_nb"] = count

    result["source"] = "BD TOPO (IGN)"
    return result


def forest(basin, progress=None):
    """Couvert forestier mesure sur la BD Foret v2.

    L'inventaire distingue plus de trente formations vegetales ; c'est le
    regroupement en onze classes qui est repris ici, seul niveau ou la
    nomenclature reste lisible dans un rapport.

    Deux totaux, et il faut les distinguer. Le couvert renvoye par la BD
    Foret comprend les landes et les formations herbacees, qui ne sont pas
    des bois ; la surface boisee au sens strict n'est que la somme des
    peuplements feuillus, coniferes et mixtes. Sur un bassin de moyenne
    montagne l'ecart atteint dix points, assez pour changer la lecture d'un
    rapport. La distinction compte aussi en hydrologie : un peuplement
    resineux n'intercepte pas la pluie comme une hetraie, et une lande
    n'intercepte presque rien.
    """
    if progress:
        progress("BD Forêt v2...")
    total = basin.area()
    if total <= 0:
        raise LandCoverError("Bassin de surface nulle.")

    by_formation = {}
    # Les polygones sont conserves avec leur forme : ils alimentent la couche
    # QGIS et la carte de la section "Occupation du sol" du rapport.
    polygones = []
    for page in wfs_pages(LAYER_FOREST, bbox=_bbox(basin), timeout=90):
        for feature in page:
            geometry = QgsGeometry(
                QgsJsonUtils.geometryFromGeoJson(
                    json.dumps(feature["geometry"]))
            )
            if geometry.isEmpty():
                continue
            clipped = geometry.intersection(basin)
            if clipped.isEmpty():
                continue
            area = clipped.area()
            if area <= 0:
                continue
            formation = str(
                feature["properties"].get("tfv_g11") or "").strip()
            by_formation[formation] = by_formation.get(formation, 0.0) + area
            polygones.append({
                "libelle": formation or "Formation non renseignée",
                "essence": str(
                    feature["properties"].get("essence") or "").strip(),
                "surface_ha": area / 1e4,
                "part_pct": 100.0 * area / total,
                "geometrie": clipped,
            })
        del page

    covered = sum(by_formation.values())
    formations = [
        {
            "libelle": name or "Formation non renseignée",
            "surface_ha": area / 1e4,
            "part_pct": 100.0 * area / total,
        }
        for name, area in sorted(by_formation.items(), key=lambda kv: -kv[1])
    ]

    result = {
        "formations": formations,
        "polygones": polygones,
        "surface_ha": covered / 1e4,
        "part_pct": 100.0 * covered / total,
        "dominante": formations[0]["libelle"] if formations else None,
        "dominante_pct": formations[0]["part_pct"] if formations else None,
        "source": "BD Forêt v2 (IGN), unité minimale 0,5 ha",
    }

    wooded = 0.0
    for key, token in FOREST_GROUPS:
        area = sum(value for name, value in by_formation.items()
                   if token in name.lower())
        wooded += area
        result[key + "_pct"] = 100.0 * area / total if area else None
    result["boisee_ha"] = wooded / 1e4
    result["boisee_pct"] = 100.0 * wooded / total
    return result


def compute(basin, with_corine=True, with_built_up=True, with_forest=True,
            progress=None):
    """Occupation du sol complete du bassin.

    Les trois sources se demandent separement : elles repondent a des
    questions differentes et ne coutent pas le meme temps, le bati de la BD
    TOPO se comptant en dizaines de milliers de polygones la ou Corine en
    rend quelques dizaines.

    Une source indisponible ne fait pas echouer l'ensemble : la partie
    manquante est renvoyee a None et le reste du rapport reste produit.
    """
    values = {"corine": None, "bati": None, "foret": None}
    if with_corine:
        try:
            values["corine"] = corine(basin, progress)
        except (GeoserviceError, LandCoverError) as exc:
            values["corine_erreur"] = str(exc)
    if with_built_up:
        try:
            values["bati"] = built_up(basin, progress)
        except GeoserviceError as exc:
            values["bati_erreur"] = str(exc)
    if with_forest:
        try:
            values["foret"] = forest(basin, progress)
        except (GeoserviceError, LandCoverError) as exc:
            values["foret_erreur"] = str(exc)
    return values
