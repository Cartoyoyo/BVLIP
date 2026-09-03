# -*- coding: utf-8 -*-
"""Acces aux services de la Geoplateforme IGN (WFS et WMS), sans cle d'API.

Un seul endroit centralise les URL, les noms de couches et la politique de
reessai : le reste du plugin n'ecrit jamais une requete HTTP a la main.

Rappels utiles, verifies sur les capacites du service :
  - WFS  : https://data.geopf.fr/wfs/ows   (couches BDTOPO_V3:*)
  - WMS  : https://data.geopf.fr/wms-r/wms (GetMap limite a 5010 x 5010 px)
  - Le seul format WMS qui renvoie de vraies altitudes est
    image/x-bil;bits=32 ; les formats image classiques renvoient une image
    d'ombrage inutilisable pour un calcul hydrologique.
"""

import json
import re
import time
import urllib.parse

from qgis.core import QgsBlockingNetworkRequest
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtNetwork import QNetworkRequest

WFS_URL = "https://data.geopf.fr/wfs/ows"
WMS_URL = "https://data.geopf.fr/wms-r/wms"

LAYER_STREAMS = "BDTOPO_V3:troncon_hydrographique"
LAYER_ZONES = "BDTOPO_V3:bassin_versant_topographique"
LAYER_DEM = "ELEVATION.ELEVATIONGRIDCOVERAGE.HIGHRES"

CRS = "EPSG:2154"
WMS_MAX_PIXELS = 5000  # marge sous la limite declaree de 5010
USER_AGENT = "BVLIP QGIS plugin (https://github.com/Cartoyoyo/BVLIP)"

DEFAULT_TIMEOUT = 60
RETRIES = 3
RETRY_DELAY = 2.0

# Pagination WFS : le service plafonne le nombre d'entites par reponse, et ne
# signale pas la troncature autrement qu'en renvoyant exactement le nombre
# demande. On pagine donc systematiquement.
WFS_PAGE_SIZE = 5000
WFS_MAX_FEATURES = 200000


class GeoserviceError(RuntimeError):
    """Echec d'acces a un service de la Geoplateforme."""


def _explain(reply):
    """Message d'erreur du service, extrait de sa reponse.

    Les services OGC renvoient un rapport d'exception XML dont seul le texte
    interesse l'utilisateur : le reste n'est que balises et espaces de noms.
    """
    try:
        body = bytes(reply.content()).decode("utf-8", "replace")
    except (AttributeError, TypeError):
        return "reponse illisible"
    found = re.search(r"<[^>]*Exception[^>]*>(.*?)</", body, re.S)
    text = found.group(1) if found else body
    text = " ".join(text.split())
    return text[:200] if text else "sans explication du service"


def _fetch(url, timeout=DEFAULT_TIMEOUT):
    """Requete HTTP GET avec reessais sur erreur reseau ou erreur serveur.

    Le telechargement passe par le gestionnaire de reseau de QGIS et non par
    urllib. Trois raisons, dans cet ordre :

      - il applique les reglages de proxy et d'authentification du poste, que
        beaucoup de collectivites imposent ; avec urllib, le plugin ne
        fonctionnerait pas derriere un proxy d'entreprise ;
      - il est prevu pour etre appele depuis un fil secondaire, ce qui est
        exactement le cas depuis que le traitement tourne en tache de fond ;
      - il ferme l'ouverture d'URL arbitraire que Bandit signale a juste
        titre, le schema n'etant plus a la main de l'appelant.

    Une erreur 4xx n'est pas rejouee : c'est une requete mal formee, la
    rejouer ne ferait que perdre du temps.
    """
    last = None
    for attempt in range(RETRIES):
        request = QNetworkRequest(QUrl(url))
        request.setHeader(QNetworkRequest.KnownHeaders.UserAgentHeader,
                          USER_AGENT)
        # Sans delai impose, une requete qui n'aboutit pas laisse la tache de
        # fond suspendue indefiniment : le bouton Annuler ne rendrait la main
        # qu'a la fin d'une etape qui ne se termine jamais.
        request.setTransferTimeout(int(timeout * 1000))
        blocking = QgsBlockingNetworkRequest()
        error = blocking.get(request)
        reply = blocking.reply()

        if error == QgsBlockingNetworkRequest.ErrorCode.NoError:
            return bytes(reply.content())

        last = blocking.errorMessage() or "erreur reseau"
        status = reply.attribute(
            QNetworkRequest.Attribute.HttpStatusCodeAttribute
        )
        if status is not None and 400 <= int(status) < 500:
            # Les services OGC repondent 400 avec un rapport d'exception qui
            # dit precisement ce qui cloche. Sans lui, l'utilisateur n'a qu'un
            # code et aucune piste.
            raise GeoserviceError(
                "Acces refuse par {0} (HTTP {1}) : {2}".format(
                    url.split("?")[0], status, _explain(reply))
            )
        if attempt < RETRIES - 1:
            time.sleep(RETRY_DELAY * (attempt + 1))
    raise GeoserviceError(
        "Acces impossible a {0} ({1})".format(url.split("?")[0], last)
    )


# --------------------------------------------------------------------- WFS

def _wfs_page(typename, bbox, page_size, start_index, resource_id, timeout):
    params = {
        "SERVICE": "WFS",
        "VERSION": "2.0.0",
        "REQUEST": "GetFeature",
        "TYPENAMES": typename,
        "SRSNAME": CRS,
        "OUTPUTFORMAT": "application/json",
        "COUNT": str(page_size),
    }
    if start_index:
        params["STARTINDEX"] = str(start_index)
    if bbox is not None:
        params["BBOX"] = "{0},{1},{2},{3},{4}".format(*bbox, CRS)
    if resource_id is not None:
        params["RESOURCEID"] = resource_id

    url = WFS_URL + "?" + urllib.parse.urlencode(params)
    payload = _fetch(url, timeout)
    try:
        return json.loads(payload.decode("utf-8")).get("features", [])
    except ValueError as exc:
        raise GeoserviceError(
            "Reponse WFS illisible pour {0} : {1}".format(typename, exc)
        )


def wfs_pages(typename, bbox=None, resource_id=None,
              page_size=WFS_PAGE_SIZE, max_features=WFS_MAX_FEATURES,
              timeout=DEFAULT_TIMEOUT):
    """Parcourt une couche WFS page par page, sans tout garder en memoire.

    bbox est un quadruplet (xmin, ymin, xmax, ymax) en Lambert 93.

    La pagination est indispensable a la justesse : sans elle, une emprise
    dense est tronquee au nombre d'entites demande, silencieusement, le
    service renvoyant une reponse valide mais incomplete. Elle sert aussi a
    l'economie de memoire quand l'appelant n'a pas besoin de toutes les
    entites en meme temps : sur un grand bassin, le bati de la BD TOPO se
    compte en dizaines de milliers de polygones dont le seul texte GeoJSON
    pese plusieurs centaines de megaoctets.
    """
    total = 0
    start = 0
    while True:
        page = _wfs_page(typename, bbox, page_size, start, resource_id, timeout)
        total += len(page)
        if page:
            yield page
        if len(page) < page_size:
            return
        if total >= max_features:
            raise GeoserviceError(
                "Plus de {0} entites dans l'emprise pour {1} : reduisez "
                "l'etendue du traitement.".format(max_features, typename)
            )
        start += page_size


def wfs_features(typename, bbox=None, resource_id=None,
                 page_size=WFS_PAGE_SIZE, max_features=WFS_MAX_FEATURES,
                 timeout=DEFAULT_TIMEOUT):
    """Renvoie toutes les entites GeoJSON d'une couche WFS, en Lambert 93.

    A reserver aux couches dont on a vraiment besoin en entier, comme le
    reseau hydrographique dont on construit le graphe. Pour un simple cumul,
    preferer wfs_pages, qui ne garde qu'une page a la fois.
    """
    features = []
    for page in wfs_pages(typename, bbox, resource_id, page_size,
                          max_features, timeout):
        features.extend(page)
    return features


# --------------------------------------------------------------------- WMS

def wms_bil_url(bbox, width, height, layer=LAYER_DEM):
    """Construit l'URL GetMap renvoyant un BIL 32 bits (altitudes reelles).

    En WMS 1.3.0 et EPSG:2154, l'axe est en ordre x,y : la bbox se donne
    donc bien xmin,ymin,xmax,ymax.
    """
    params = {
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "REQUEST": "GetMap",
        "LAYERS": layer,
        "STYLES": "",
        "CRS": CRS,
        "BBOX": "{0},{1},{2},{3}".format(*bbox),
        "WIDTH": str(width),
        "HEIGHT": str(height),
        "FORMAT": "image/x-bil;bits=32",
        "TRANSPARENT": "FALSE",
    }
    return WMS_URL + "?" + urllib.parse.urlencode(params)


def wms_bil(bbox, width, height, layer=LAYER_DEM, timeout=DEFAULT_TIMEOUT):
    """Telecharge une dalle d'altitudes et renvoie les octets BIL bruts.

    Le service renvoie parfois une image d'erreur XML avec un code 200 : on
    verifie donc la taille attendue, quatre octets par pixel.
    """
    expected = width * height * 4
    payload = _fetch(wms_bil_url(bbox, width, height, layer), timeout)
    if len(payload) != expected:
        head = payload[:200].decode("utf-8", "replace")
        raise GeoserviceError(
            "Reponse WMS inattendue : {0} octets au lieu de {1}. Debut de la "
            "reponse : {2}".format(len(payload), expected, head)
        )
    return payload
