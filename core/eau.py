# -*- coding: utf-8 -*-
"""Gestion de l'eau dans le bassin : SAGE et surveillance des crues.

Deux donnees qui ne decrivent pas le milieu mais le cadre dans lequel on le
gere, et que tout diagnostic de bassin versant cite en premier :

  SAGE        schema d'amenagement et de gestion des eaux. Son perimetre dit
              quelle commission locale de l'eau est competente, et donc a
              qui s'adresser. Servi par le Sandre, en WFS 1.1.
  Vigicrues   reseau de surveillance reglementaire des crues de l'Etat : les
              troncons de cours d'eau surveilles et les stations qui les
              mesurent. Servi par la Geoplateforme. Un bassin dont aucun
              troncon n'est surveille n'est pas pour autant sans risque : il
              n'est simplement pas couvert par la vigilance nationale.
"""

from . import sandre
from .clip import PreparedBasin, geometry_of
from .geoservices import GeoserviceError, wfs_pages

LAYER_SAGE = "sa:Sage_FXX"
LAYER_TRONCONS = "VIGICRUES:troncons"
LAYER_STATIONS = "VIGICRUES:stations"

SOURCE_SAGE = "Périmètres des SAGE (Sandre)"

# Part du bassin en dessous de laquelle un SAGE n'est qu'un lisere de bord,
# du a l'ecart entre son contour et celui du bassin.
SAGE_MIN_PCT = 1.0
SOURCE_VIGICRUES = "Vigicrues — tronçons et stations (SCHAPI, Géoplateforme)"

def _bbox(basin):
    box = basin.boundingBox()
    return (box.xMinimum(), box.yMinimum(), box.xMaximum(), box.yMaximum())


def _etat(code):
    """Etat d'avancement du SAGE, en code brut.

    Le service ne sert que le code ("4.1"), pas son libelle, et la
    nomenclature n'est pas interrogeable a cote : le code est rendu tel quel
    plutot que traduit de memoire, comme le type d'ouvrage du ROE.
    """
    code = str(code or "").strip()
    return "code Sandre {0}".format(code) if code else None


def sage(basin, progress=None):
    """Perimetres de SAGE recoupant le bassin, et la part qu'ils en couvrent.

    Un bassin peut chevaucher deux SAGE sur une ligne de partage des eaux
    approximative : les deux sont rendus, chacun avec sa part. La part
    couverte totale est une union, les perimetres de deux SAGE ne se
    recouvrant en principe pas mais rien ne le garantit.
    """
    if progress:
        progress("SAGE (Sandre)...")
    total = basin.area()
    records = []
    shapes = []
    for feature, geometry in sandre.features_in(LAYER_SAGE, basin):
        clipped = geometry.intersection(basin)
        if clipped.isEmpty() or clipped.area() <= 0:
            continue
        attributes = sandre.attributes(feature)
        area = clipped.area()
        records.append({
            "code": attributes.get("CodeNatZone"),
            "nom": attributes.get("NomZone"),
            "etat": _etat(attributes.get("EtatAvancementSage")),
            "surface_ha": area / 1e4,
            "part_pct": 100.0 * area / total if total else None,
        })
        shapes.append(clipped)
    records.sort(key=lambda r: -r["surface_ha"])
    covered = 0.0
    if shapes:
        from qgis.core import QgsGeometry
        covered = QgsGeometry.unaryUnion(shapes).area()
    # Le champ du bassin ne nomme que les SAGE qui le couvrent vraiment. Les
    # autres ne sont que des liseres de bord : releve sur la Besbre, trois
    # SAGE voisins pour 0,8 % du bassin a eux trois, que le champ aurait
    # annonces comme "couvrant le bassin". Ils restent dans le detail.
    principaux = [r for r in records
                  if r["part_pct"] is not None
                  and r["part_pct"] >= SAGE_MIN_PCT]
    return {
        "nb": len(records),
        "noms": ", ".join(str(r["nom"]) for r in principaux
                          if r["nom"]) or None,
        "part_pct": min(100.0, 100.0 * covered / total) if total else None,
        "sages": records,
        "source": SOURCE_SAGE,
    }


def vigicrues(basin, progress=None):
    """Troncons surveilles par Vigicrues dans le bassin, et leurs stations."""
    if progress:
        progress("Vigicrues...")
    prepared = PreparedBasin(basin)
    bbox = _bbox(basin)

    troncons = {}
    lignes = []
    for page in wfs_pages(LAYER_TRONCONS, bbox=bbox, timeout=90):
        for feature in page:
            clipped = prepared.clip(geometry_of(feature))
            if clipped is None or clipped.length() <= 0:
                continue
            properties = feature.get("properties") or {}
            code = properties.get("cdentcru") or properties.get("id")
            nom = properties.get("lbentcru") or code
            entry = troncons.setdefault(code, {
                "code": code, "nom": nom, "longueur_km": 0.0,
            })
            entry["longueur_km"] += clipped.length() / 1000.0
            lignes.append({"code": code, "nom": nom, "geometrie": clipped})
        del page

    stations = []
    for page in wfs_pages(LAYER_STATIONS, bbox=bbox, timeout=90):
        for feature in page:
            clipped = prepared.clip(geometry_of(feature))
            if clipped is None:
                continue
            properties = feature.get("properties") or {}
            point = clipped.asPoint()
            stations.append({
                "code": properties.get("cdentcru"),
                "nom": properties.get("lbentcru"),
                "cours_d_eau": properties.get("lbentitehy"),
                "x": point.x(),
                "y": point.y(),
            })
        del page

    liste = sorted(troncons.values(), key=lambda t: -t["longueur_km"])
    stations.sort(key=lambda s: str(s["code"] or ""))
    return {
        "longueur_km": sum(t["longueur_km"] for t in liste),
        "nb_troncons": len(liste),
        "troncons": liste,
        "lignes": lignes,
        "nb_stations": len(stations),
        "stations": stations,
        "source": SOURCE_VIGICRUES,
    }


def compute(basin, with_sage=True, with_vigicrues=True, progress=None):
    """Cadre de gestion de l'eau du bassin.

    Une source indisponible laisse sa partie a None sans emporter l'autre.
    """
    values = {"sage": None, "vigicrues": None, "erreurs": []}
    if with_sage:
        try:
            values["sage"] = sage(basin, progress)
        except Exception as exc:      # noqa: BLE001 - toute panne du Sandre
            values["erreurs"].append("SAGE : {0}".format(exc))
    if with_vigicrues:
        try:
            values["vigicrues"] = vigicrues(basin, progress)
        except GeoserviceError as exc:
            values["erreurs"].append("Vigicrues : {0}".format(exc))
    return values
