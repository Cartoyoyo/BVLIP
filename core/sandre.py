# -*- coding: utf-8 -*-
"""Acces au serveur cartographique du Sandre (eaufrance).

Le Sandre est le referentiel national de l'eau. Il porte ce que l'IGN n'a
pas : les masses d'eau au sens de la directive cadre, les hydroecoregions,
les obstacles a l'ecoulement, les zonages reglementaires lies a l'eau.

Son service ne parle que le WFS 1.1 et ne sert pas de GeoJSON : on passe
donc par le client WFS de QGIS plutot que par des requetes construites a la
main, comme le fait geoservices pour la Geoplateforme. Ce module est le
pendant Sandre de celui-la, et la seule porte d'entree du plugin vers ce
service.

Deux limites du serveur commandent la facon de s'en servir :

  - aucun filtre attributaire n'est applique cote serveur. Une couche
    interrogee par expression est rapatriee en entier, puis filtree ici :
    quarante secondes pour une ligne sur la couche des masses d'eau
    riviere. A reserver aux cas ou l'emprise ne suffit pas ;
  - le filtre par emprise, lui, fonctionne, a condition de le declarer dans
    l'URI avec restrictToRequestBBOX. Sans lui, QGIS telecharge la couche
    nationale avant de filtrer localement.
"""

from qgis.core import (
    QgsFeatureRequest, QgsGeometry, QgsPointXY, QgsRectangle, QgsVectorLayer,
)

URL = "https://services.sandre.eaufrance.fr/geo/sandre"


def layer(typename):
    """Couche WFS Sandre prete a etre interrogee, ou None si elle echoue.

    Renvoyer None plutot que lever : une couche indisponible prive le rapport
    d'une ligne, elle n'a pas a faire echouer le traitement.
    """
    uri = (
        "restrictToRequestBBOX='1' srsname='EPSG:2154' typename='{0}' "
        "url='{1}' version='1.1.0'"
    ).format(typename, URL)
    result = QgsVectorLayer(uri, typename, "WFS")
    return result if result.isValid() else None


def attributes(feature):
    """Attributs non vides d'une entite, en dictionnaire."""
    return {
        name: feature[name]
        for name in feature.fields().names()
        if feature[name] not in (None, "")
    }


def as_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def as_bool(value):
    """Booleen Sandre, servi tantot en oui/non, tantot en 0/1."""
    if value in (None, ""):
        return None
    text = str(value).strip().lower()
    if text in ("1", "true", "oui", "o", "yes", "y"):
        return True
    if text in ("0", "false", "non", "n", "no"):
        return False
    return None


def features_in(typename, geometry):
    """Entites d'une couche Sandre rencontrant la geometrie donnee.

    Le service filtre sur l'emprise, jamais sur la forme : le test
    d'intersection avec le polygone reel se fait donc ici. La difference
    n'est pas cosmetique sur un bassin versant, dont l'emprise rectangulaire
    fait couramment le double de la surface.
    """
    source = layer(typename)
    if source is None:
        return
    box = geometry.boundingBox()
    request = QgsFeatureRequest().setFilterRect(
        QgsRectangle(box.xMinimum(), box.yMinimum(),
                     box.xMaximum(), box.yMaximum())
    )
    for feature in source.getFeatures(request):
        shape = feature.geometry()
        if shape.isEmpty() or not shape.intersects(geometry):
            continue
        yield feature, shape


def features_at(typename, x, y, radius=0.0):
    """Entites d'une couche Sandre contenant le point, ou proches de lui.

    Le rayon sert aux couches dont le decoupage ne couvre pas exactement le
    territoire : un exutoire tombe parfois quelques metres en dehors du
    polygone qui le concerne. Les entites qui contiennent vraiment le point
    viennent en premier.
    """
    source = layer(typename)
    if source is None:
        return []
    point = QgsGeometry.fromPointXY(QgsPointXY(x, y))
    span = max(radius, 1.0)
    request = QgsFeatureRequest().setFilterRect(
        QgsRectangle(x - span, y - span, x + span, y + span)
    )
    inside = []
    near = []
    for feature in source.getFeatures(request):
        shape = feature.geometry()
        if shape.isEmpty():
            continue
        if shape.contains(point):
            inside.append(feature)
        elif radius and shape.distance(point) <= radius:
            near.append((shape.distance(point), feature))
    return inside or [f for _d, f in sorted(near, key=lambda p: p[0])]
