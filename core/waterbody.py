# -*- coding: utf-8 -*-
"""Rattachement de l'exutoire a la masse d'eau DCE dont il releve.

Le referentiel des masses d'eau est celui du Sandre, pas celui de l'IGN : la
couche equivalente de la Geoplateforme ne couvre qu'un millier d'entites et
laisse de grandes parties du territoire sans reponse.

Deux couches sont interrogees :
  BVSpeMasseDEauSurface   bassin versant specifique de chaque masse d'eau de
                          surface ; c'est un polygone, donc le rattachement se
                          fait par simple appartenance de l'exutoire
  MasseDEauRiviere        la masse d'eau elle-meme, interrogee par son code
                          pour recuperer nom, type, bassin DCE et Strahler

Le service Sandre ne parle que le WFS 1.1 et ne sert pas de GeoJSON : on passe
donc par le client WFS de QGIS plutot que par des requetes construites a la
main.
"""

from qgis.core import (
    QgsFeatureRequest, QgsGeometry, QgsPointXY, QgsRectangle, QgsVectorLayer,
)

SANDRE_URL = "https://services.sandre.eaufrance.fr/geo/sandre"

# Versions retenues : le bassin versant specifique n'existe qu'en etat des
# lieux 2019, la masse d'eau riviere est prise dans le rapportage le plus
# recent.
LAYER_CATCHMENT = "sa:BVSpeMasseDEauSurface_VEDL2019_FXX"
LAYER_RIVER = "sa:MasseDEauRiviere_VRAP2022_FXX"

SEARCH_RADIUS = 250.0  # m, autour de l'exutoire


def _layer(typename):
    uri = (
        "restrictToRequestBBOX='1' srsname='EPSG:2154' typename='{0}' "
        "url='{1}' version='1.1.0'"
    ).format(typename, SANDRE_URL)
    layer = QgsVectorLayer(uri, typename, "WFS")
    return layer if layer.isValid() else None


def _attributes(feature):
    return {
        name: feature[name]
        for name in feature.fields().names()
        if feature[name] not in (None, "")
    }


def _as_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def find_water_body(x, y, radius=SEARCH_RADIUS, detailed=False):
    """Renvoie la masse d'eau DCE dont releve le point, ou None.

    Le dictionnaire renvoye est toujours de la meme forme, meme si
    l'enrichissement par la couche des masses d'eau riviere echoue : le code
    et le nom du bassin versant specifique suffisent a identifier la masse
    d'eau, le reste est du confort.

    detailed declenche cet enrichissement (type, longueur, bassin DCE,
    Strahler). Il est desactive par defaut car il coute environ quarante
    secondes : le service Sandre n'applique aucun filtre attributaire cote
    serveur, ni par CQL ni par requete SQL, si bien que la couche nationale
    des masses d'eau riviere est rapatriee en entier pour n'en retenir
    qu'une ligne.
    """
    catchments = _layer(LAYER_CATCHMENT)
    if catchments is None:
        return None

    point = QgsGeometry.fromPointXY(QgsPointXY(x, y))
    rectangle = QgsRectangle(x - radius, y - radius, x + radius, y + radius)
    request = QgsFeatureRequest().setFilterRect(rectangle)

    chosen = None
    fallback = None
    for feature in catchments.getFeatures(request):
        geometry = feature.geometry()
        if geometry.contains(point):
            chosen = feature
            break
        distance = geometry.distance(point)
        if fallback is None or distance < fallback[0]:
            fallback = (distance, feature)

    exact = chosen is not None
    if chosen is None:
        if fallback is None:
            return None
        chosen = fallback[1]

    attributes = _attributes(chosen)
    result = {
        "code_eu": attributes.get("CdEuMasseDEau"),
        "code": attributes.get("CdMasseDEau"),
        "nom_bv": attributes.get("NomBVSpeMDO"),
        "surface_bv_km2": _as_float(attributes.get("SurfaceBVSpeMDO")),
        "precision_bv": attributes.get("NiveauPrecisionBVSpeMDO"),
        "categorie": attributes.get("CdCategorieMasseDEau"),
        "exutoire_dans_le_bv": exact,
        "nom": None,
        "type": None,
        "longueur_km": None,
        "bassin_dce": None,
        "sous_bassin_dce": None,
        "strahler_max": None,
    }

    code_eu = result["code_eu"]
    if detailed and code_eu:
        result.update(_river_details(code_eu))
    return result


def _river_details(code_eu):
    """Complete avec les attributs de la masse d'eau riviere elle-meme.

    Interrogee par expression sur le code : la masse d'eau est un lineaire qui
    peut se trouver a plusieurs kilometres de l'exutoire, une recherche par
    emprise ne la trouverait pas.
    """
    empty = {}
    rivers = _layer(LAYER_RIVER)
    if rivers is None:
        return empty
    expression = "\"CdEuMasseDEau\" = '{0}'".format(code_eu.replace("'", "''"))
    request = QgsFeatureRequest().setFilterExpression(expression)
    for feature in rivers.getFeatures(request):
        attributes = _attributes(feature)
        return {
            "nom": attributes.get("NomMasseDEau"),
            "type": attributes.get("TypeMasseDEauRiviere"),
            "longueur_km": _as_float(attributes.get("LongueurTotKm")),
            "bassin_dce": attributes.get("CdEuBassinDCE"),
            "sous_bassin_dce": attributes.get("CdEuSsBassinDCEAdmin"),
            "strahler_max": attributes.get("StrahlMax"),
        }
    return empty
