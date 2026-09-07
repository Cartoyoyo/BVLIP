# -*- coding: utf-8 -*-
"""Estimation de la population du bassin versant.

Aucun recensement ne dit combien d'habitants vivent dans un bassin versant :
la population est un attribut communal, et un bassin recoupe rarement une
commune en entier. Ce module reconstitue une estimation en deux temps, par
commune ADMIN EXPRESS (IGN) recoupant le bassin :

  - le nombre de logements du bati BD TOPO dans la part du bassin qui touche
    la commune, contre le nombre de logements de la commune entiere. Le champ
    nombre_de_logements ne surestime pas comme le ferait un compte de
    batiments : un garage ou un hangar agricole y vaut zero, l'IGN le
    calculant a partir des seules parties d'evaluation cadastrale marquees
    habitation ;
  - cette part, appliquee a la population officielle de la commune (attribut
    ADMIN EXPRESS COG, lui-meme repris du recensement).

Une commune coupee en deux par le bassin ne compte donc que pour la part de
son bati qui s'y trouve, pas pour sa population entiere. L'hypothese qui reste
posee est que la densite de logements est comparable dans et hors bassin - ce
qui n'est pas garanti pres d'un bourg-centre a cheval sur la limite, mais
demeure la meilleure approximation accessible sans microdonnees INSEE
geolocalisees, qui n'existent pas en donnee ouverte a cette echelle.
"""

import json

from qgis.core import QgsGeometry, QgsJsonUtils

from .geoservices import GeoserviceError, wfs_pages
from .landcover import LAYER_BUILDINGS

LAYER_COMMUNE = "ADMINEXPRESS-COG.LATEST:commune"

# Plafond du releve detaille, comme pour les obstacles et les STEU : un
# bassin peut toucher beaucoup de communes en bordure, et chacune devient une
# ligne dans le rapport.
MAX_DETAIL = 200

SOURCE = ("Bâti BD TOPO (IGN) et communes ADMIN EXPRESS COG (IGN) — "
         "estimation, non un recensement")


def _bbox(geometry):
    box = geometry.boundingBox()
    return (box.xMinimum(), box.yMinimum(), box.xMaximum(), box.yMaximum())


def _geometry_of(feature):
    geometry = QgsGeometry(
        QgsJsonUtils.geometryFromGeoJson(json.dumps(feature["geometry"]))
    )
    return None if geometry.isEmpty() else geometry


def communes_touching(basin):
    """Communes ADMIN EXPRESS dont le polygone recoupe le bassin."""
    found = []
    for page in wfs_pages(LAYER_COMMUNE, bbox=_bbox(basin)):
        for feature in page:
            geometry = _geometry_of(feature)
            if geometry is None or not geometry.intersects(basin):
                continue
            properties = feature["properties"]
            found.append({
                "code": properties.get("code_insee"),
                "nom": properties.get("nom_officiel"),
                "population": properties.get("population"),
                "geometrie": geometry,
            })
    return found


def _sum_logements(bbox, clip_geometry):
    """Logements BD TOPO dont le batiment recoupe la geometrie donnee."""
    total = 0
    for page in wfs_pages(LAYER_BUILDINGS, bbox=bbox):
        for feature in page:
            logements = feature["properties"].get("nombre_de_logements")
            if not logements:
                continue
            geometry = _geometry_of(feature)
            if geometry is not None and geometry.intersects(clip_geometry):
                total += int(logements)
        del page
    return total


def _logements_by_commune(basin, communes):
    """Logements du bassin, repartis par commune.

    Un meme batiment n'est credite qu'a une seule commune - la premiere qui
    le recoupe - pour ne jamais compter un logement deux fois : la frontiere
    communale coupe en theorie de tres rares batiments, jamais un logement.
    """
    by_code = {c["code"]: 0 for c in communes}
    for page in wfs_pages(LAYER_BUILDINGS, bbox=_bbox(basin)):
        for feature in page:
            logements = feature["properties"].get("nombre_de_logements")
            if not logements:
                continue
            geometry = _geometry_of(feature)
            if geometry is None or not geometry.intersects(basin):
                continue
            for commune in communes:
                if geometry.intersects(commune["geometrie"]):
                    by_code[commune["code"]] += int(logements)
                    break
        del page
    return by_code


def estimate(basin, progress=None):
    """Estimation de population du bassin, commune par commune."""
    if progress:
        progress("Communes ADMIN EXPRESS...")
    communes = communes_touching(basin)
    if not communes:
        return {"nb_communes": 0, "nb_communes_estimees": 0,
                "population_estimee": None, "communes": [], "source": SOURCE}

    if progress:
        progress("Logements du bassin, par commune...")
    logements_bv = _logements_by_commune(basin, communes)

    records = []
    total = 0.0
    connues = 0
    for commune in communes:
        if progress:
            progress("Logements de {0}...".format(commune["nom"] or
                                                   commune["code"]))
        code = commune["code"]
        bv = logements_bv.get(code, 0)
        try:
            entiers = _sum_logements(_bbox(commune["geometrie"]),
                                     commune["geometrie"])
        except GeoserviceError:
            entiers = None

        part_pct = None
        population_estimee = None
        if entiers:
            part_pct = 100.0 * bv / entiers
            if commune["population"] is not None:
                population_estimee = commune["population"] * bv / entiers
                total += population_estimee
                connues += 1

        records.append({
            "code": code,
            "nom": commune["nom"],
            "population": commune["population"],
            "logements_bv": bv,
            "logements_commune": entiers,
            "part_logements_pct": part_pct,
            "population_estimee": population_estimee,
        })

    records.sort(key=lambda r: -(r["population_estimee"] or 0.0))

    return {
        "nb_communes": len(records),
        "nb_communes_estimees": connues,
        "population_estimee": total if connues else None,
        "communes": records[:MAX_DETAIL],
        "source": SOURCE,
    }


def compute(basin, with_population=True, progress=None):
    """Releve de population du bassin.

    Une couche indisponible laisse la partie a None sans faire echouer le
    reste, comme pour les obstacles et les STEU : le service rend son
    service inegalement selon les heures.
    """
    values = {"population": None, "erreurs": []}
    if not with_population:
        return values
    try:
        values["population"] = estimate(basin, progress=progress)
    except Exception as exc:      # noqa: BLE001 - toute panne du service
        values["erreurs"].append("Population estimée : {0}".format(exc))
    return values
