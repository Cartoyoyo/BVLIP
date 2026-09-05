# -*- coding: utf-8 -*-
"""Rattachement de l'exutoire aux referentiels de l'eau dont il releve.

Le referentiel des masses d'eau est celui du Sandre, pas celui de l'IGN : la
couche equivalente de la Geoplateforme ne couvre qu'un millier d'entites et
laisse de grandes parties du territoire sans reponse.

Quatre couches sont interrogees :
  BVSpeMasseDEauSurface   bassin versant specifique de chaque masse d'eau de
                          surface ; c'est un polygone, donc le rattachement se
                          fait par simple appartenance de l'exutoire
  MasseDEauRiviere        la masse d'eau elle-meme, interrogee par son code
                          pour recuperer nom, type, bassin DCE et Strahler
  MasseDEauSouterraine    la nappe sous l'exutoire. Elle ne se substitue pas a
                          la masse d'eau de surface : les deux repondent a des
                          questions differentes, et un bassin versant
                          topographique ne coincide pas avec son bassin
                          hydrogeologique - d'autant moins qu'il est karstique.
  Hydroecoregion 1 et 2   le cadre de comparaison de la DCE. Un bassin ne
                          s'apprecie pas dans l'absolu mais par rapport a ceux
                          de son hydroecoregion, qui partagent geologie, relief
                          et climat. Deux lignes, et le lecteur sait a quoi
                          comparer les chiffres du dessus.

L'acces au service Sandre est dans le module sandre : lui seul sait que ce
serveur ne parle que le WFS 1.1 et ne sert pas de GeoJSON.
"""

from qgis.core import QgsFeatureRequest, QgsGeometry, QgsPointXY, QgsRectangle

from . import sandre

# Versions retenues : le bassin versant specifique n'existe qu'en etat des
# lieux 2019, la masse d'eau riviere est prise dans le rapportage le plus
# recent.
LAYER_CATCHMENT = "sa:BVSpeMasseDEauSurface_VEDL2019_FXX"
LAYER_RIVER = "sa:MasseDEauRiviere_VRAP2022_FXX"
LAYER_GROUNDWATER = "sa:MasseDEauSouterraine_VEDL2019_FXX"
LAYER_HER1 = "sa:Hydroecoregion1_FXX"
LAYER_HER2 = "sa:Hydroecoregion2_FXX"

SEARCH_RADIUS = 250.0  # m, autour de l'exutoire

_layer = sandre.layer
_attributes = sandre.attributes
_as_float = sandre.as_float


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


def find_groundwater(x, y, radius=SEARCH_RADIUS):
    """Masse d'eau souterraine sous l'exutoire, ou None.

    Les masses d'eau souterraines se superposent : une nappe libre de surface
    et un aquifere profond peuvent couvrir le meme point, et le referentiel
    les livre comme deux polygones distincts. On retient celle qui affleure -
    la moins etendue en surface d'affleurement - parce que c'est celle qui
    echange avec le cours d'eau, donc celle qui interesse un bassin versant.
    """
    found = sandre.features_at(LAYER_GROUNDWATER, x, y, radius)
    if not found:
        return None

    def surface(feature):
        value = _as_float(_attributes(feature).get("SurfaceAffKm"))
        return value if value is not None else float("inf")

    attributes = _attributes(min(found, key=surface))
    return {
        "code_eu": attributes.get("CdEuMasseDEau"),
        "code": attributes.get("CdMasseDEau"),
        "nom": attributes.get("NomMasseDEau"),
        "type": attributes.get("TypeMasseDEauSouterraine"),
        "nature_ecoulement": attributes.get("NatureEcoulement"),
        "milieu": attributes.get("TypePrincipalMilieu"),
        "karstique": sandre.as_bool(attributes.get("Karstique")),
        "surface_affleurante_km2": _as_float(
            attributes.get("SurfaceAffKm")),
        "surface_totale_km2": _as_float(attributes.get("SurfaceTotaleKm")),
        "nb_recouvrantes": len(found),
    }


def find_hydroecoregion(x, y, radius=SEARCH_RADIUS):
    """Hydroecoregions de niveau 1 et 2 auxquelles l'exutoire appartient.

    Le niveau 1 decoupe la France en une vingtaine d'ensembles - Massif
    central nord, Alpes internes, Tables calcaires - et le niveau 2 les
    subdivise. C'est la grille de lecture de la DCE : les valeurs de
    reference d'un cours d'eau y sont etablies, et deux bassins de HER
    differentes ne se comparent pas.
    """
    result = {"her1_code": None, "her1_nom": None,
              "her2_code": None, "her2_nom": None}
    # Les deux couches numerotent leurs champs : CdHER1 et NomHER1 sur le
    # niveau 1, CdHER2 et NomHER2 sur le niveau 2. Les noms sans chiffre sont
    # gardes en secours, le serveur ayant deja change de schema par le passe.
    for typename, level in ((LAYER_HER1, 1), (LAYER_HER2, 2)):
        found = sandre.features_at(typename, x, y, radius)
        if not found:
            continue
        attributes = _attributes(found[0])
        code = attributes.get("CdHER{0}".format(level), attributes.get("CdHER"))
        name = attributes.get("NomHER{0}".format(level),
                              attributes.get("NomHER"))
        result["her{0}_code".format(level)] = (
            None if code is None else str(code))
        result["her{0}_nom".format(level)] = name
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
