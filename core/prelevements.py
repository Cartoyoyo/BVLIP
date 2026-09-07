# -*- coding: utf-8 -*-
"""Prelevements d'eau du bassin, cote amont de ce que les STEU rejettent en aval.

Hub'Eau (Office francais de la biodiversite) publie la Banque Nationale des
Prelevements en Eau (BNPE) : un ouvrage de prelevement par point, un volume
annuel declare par usage - eau potable, irrigation, industrie, energie. C'est
une mesure directe de la pression anthropique sur la ressource, complementaire
des STEU qui ne disent que ce qui est rendu au milieu, jamais ce qui en est
retire.

Hub'Eau ne filtre pas par emprise geographique, seulement par commune : le
releve part donc des communes ADMIN EXPRESS qui recoupent le bassin - celles
que core.population interroge deja pour la population - puis ne garde que les
ouvrages dont le point tombe reellement dans le bassin. La commune n'est
qu'un filtre grossier en amont de la requete, jamais le critere d'appartenance
retenu : les coordonnees de chaque ouvrage sont exactes et le testent
directement, comme un ROE ou une STEU.

Un ouvrage porte plusieurs annees de volume, une ligne par annee declaree ;
seule la plus recente connue est retenue ici, comme la charge d'une STEU ne
retient que son dernier releve d'autosurveillance.
"""

import json
import urllib.parse

from qgis.core import (
    QgsBlockingNetworkRequest, QgsCoordinateReferenceSystem,
    QgsCoordinateTransform, QgsGeometry, QgsPointXY, QgsProject,
)
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtNetwork import QNetworkRequest

from .population import communes_touching

API_URL = "https://hubeau.eaufrance.fr/api/v1/prelevements/chroniques"
USER_AGENT = b"BVLIP QGIS plugin (https://github.com/Cartoyoyo/BVLIP)"
PAGE_SIZE = 500
TIMEOUT = 60

# Communes par requete : Hub'Eau ne documente pas de limite, mais une URL trop
# longue se heurte a celle des serveurs intermediaires bien avant celle du
# service lui-meme.
CHUNK = 100

# Plafond du releve detaille, comme pour les obstacles, les STEU et les
# communes : un grand bassin industriel peut porter plusieurs centaines
# d'ouvrages, et chacun devient une ligne dans le rapport.
MAX_DETAIL = 300

SOURCE = ("Prélèvements en eau (Hub'Eau / BNPE, Office français de la "
         "biodiversité) — dernière année connue par ouvrage")

WGS84 = QgsCoordinateReferenceSystem("EPSG:4326")
LAMBERT93 = QgsCoordinateReferenceSystem("EPSG:2154")


class HubeauError(Exception):
    """Le service Hub'Eau n'a pas repondu ou a repondu une donnee illisible."""


def _fetch(url):
    request = QNetworkRequest(QUrl(url))
    request.setRawHeader(b"User-Agent", USER_AGENT)
    blocking = QgsBlockingNetworkRequest()
    error = blocking.get(request)
    if error != QgsBlockingNetworkRequest.ErrorCode.NoError:
        raise HubeauError(blocking.errorMessage() or "erreur réseau Hub'Eau")
    payload = bytes(blocking.reply().content())
    try:
        return json.loads(payload.decode("utf-8"))
    except ValueError as exc:
        raise HubeauError(
            "réponse Hub'Eau illisible : {0}".format(exc)
        ) from exc


def _chunks(items, size):
    for start in range(0, len(items), size):
        yield items[start:start + size]


def _records(codes):
    """Chroniques de prelevement des communes donnees, toutes pages."""
    for chunk in _chunks(codes, CHUNK):
        params = {
            "code_commune_insee": ",".join(chunk),
            "size": str(PAGE_SIZE),
        }
        url = API_URL + "?" + urllib.parse.urlencode(params)
        while url:
            payload = _fetch(url)
            for record in payload.get("data") or []:
                yield record
            url = payload.get("next")


def withdrawals(basin, progress=None):
    """Prelevements d'eau du bassin, un ouvrage par point retenu."""
    if progress:
        progress("Communes ADMIN EXPRESS...")
    codes = [c["code"] for c in communes_touching(basin) if c.get("code")]
    if not codes:
        return {"nb": 0, "volume_total_m3": None, "annee_recente": None,
                "par_usage": [], "ouvrages": [], "source": SOURCE}

    if progress:
        progress("Prélèvements d'eau (Hub'Eau)...")
    latest = {}
    for record in _records(codes):
        code = record.get("code_ouvrage")
        annee = record.get("annee")
        if not code or annee is None:
            continue
        current = latest.get(code)
        if current is None or annee > current["annee"]:
            latest[code] = record

    transform = QgsCoordinateTransform(WGS84, LAMBERT93,
                                       QgsProject.instance())
    kept = []
    for record in latest.values():
        longitude = record.get("longitude")
        latitude = record.get("latitude")
        if longitude is None or latitude is None:
            continue
        point = QgsGeometry.fromPointXY(QgsPointXY(longitude, latitude))
        point.transform(transform)
        if not point.intersects(basin):
            continue
        position = point.asPoint()
        kept.append({
            "code": record.get("code_ouvrage"),
            "nom": record.get("nom_ouvrage"),
            "annee": record.get("annee"),
            "volume_m3": record.get("volume"),
            "usage": record.get("libelle_usage"),
            "commune": record.get("nom_commune"),
            "x": position.x(),
            "y": position.y(),
        })

    kept.sort(key=lambda r: -(r["volume_m3"] or 0.0))

    par_usage = {}
    volume_total = 0.0
    for record in kept:
        volume = record["volume_m3"] or 0.0
        volume_total += volume
        usage = record["usage"] or "Usage non renseigné"
        par_usage[usage] = par_usage.get(usage, 0.0) + volume

    return {
        "nb": len(kept),
        "volume_total_m3": volume_total if kept else None,
        "annee_recente": max((r["annee"] for r in kept), default=None),
        "par_usage": sorted(
            ({"usage": usage, "volume_m3": volume}
             for usage, volume in par_usage.items()),
            key=lambda r: -r["volume_m3"],
        ),
        "ouvrages": kept[:MAX_DETAIL],
        "source": SOURCE,
    }


def compute(basin, with_prelevements=True, progress=None):
    """Releve des prelevements d'eau du bassin.

    Une couche indisponible laisse la partie a None sans faire echouer le
    reste, comme pour les obstacles, les STEU et la population : le service
    rend son service inegalement selon les heures.
    """
    values = {"prelevements": None, "erreurs": []}
    if not with_prelevements:
        return values
    try:
        values["prelevements"] = withdrawals(basin, progress=progress)
    except Exception as exc:      # noqa: BLE001 - toute panne du service
        values["erreurs"].append("Prélèvements d'eau : {0}".format(exc))
    return values
