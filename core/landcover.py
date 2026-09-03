# -*- coding: utf-8 -*-
"""Occupation du sol du bassin versant.

Deux sources, complementaires plutot que concurrentes :

  Corine Land Cover 2018   couverture complete et nomenclature normalisee, mais
                           unite minimale de collecte de 25 ha. Sur un petit
                           bassin, elle donne la structure d'ensemble et rien
                           de plus.
  BD TOPO                  batiments et zones d'habitation, au metre pres.
                           Indispensable ici : CLC efface purement et
                           simplement les hameaux, et annoncerait 0 % d'urbain
                           sur un bassin qui en compte plusieurs.

Les deux ne sont pas additionnees. CLC fournit la repartition, qui somme a
100 %, et la BD TOPO un indicateur de bati mesure independamment. Les melanger
reviendrait a compter deux fois les memes surfaces.
"""

import json

from qgis.core import QgsGeometry, QgsJsonUtils

from .geoservices import GeoserviceError, wfs_pages

LAYER_CLC = "LANDCOVER.CLC18_FR:clc18_fr"
LAYER_BUILDINGS = "BDTOPO_V3:batiment"
LAYER_SETTLEMENTS = "BDTOPO_V3:zone_d_habitation"

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


def compute(basin, with_built_up=True, progress=None):
    """Occupation du sol complete du bassin.

    Une source indisponible ne fait pas echouer l'ensemble : la partie
    manquante est renvoyee a None et le reste du rapport reste produit.
    """
    values = {"corine": None, "bati": None}
    try:
        values["corine"] = corine(basin, progress)
    except (GeoserviceError, LandCoverError) as exc:
        values["corine_erreur"] = str(exc)
    if with_built_up:
        try:
            values["bati"] = built_up(basin, progress)
        except GeoserviceError as exc:
            values["bati_erreur"] = str(exc)
    return values
