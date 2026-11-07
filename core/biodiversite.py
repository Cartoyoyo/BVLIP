# -*- coding: utf-8 -*-
"""Biodiversite observee dans le bassin, d'apres le GBIF.

Le GBIF - Global Biodiversity Information Facility - agrege les
observations naturalistes publiees dans le monde, dont celles de l'INPN et
des grands programmes participatifs francais. On ne rapatrie ici aucun
point : seulement des comptes, par grand groupe, d'observations et
d'especes distinctes.

Deux reserves, que le rapport rappelle :

  - c'est un effort d'observation autant qu'une richesse. Un bassin
    parcouru par un club naturaliste actif compte dix fois plus d'especes
    qu'un bassin voisin aussi riche mais peu visite ;
  - les groupes se recouvrent la ou la classification le veut : les
    chauves-souris sont des mammiferes, et figurent dans les deux lignes.

Le bassin est envoye au service comme polygone en WGS 84, simplifie jusqu'a
tenir dans une URL. La simplification deplace le contour de quelques
dizaines de metres au plus : negligeable devant la precision des
observations elles-memes, souvent arrondie au kilometre.
"""

import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

from qgis.core import (
    QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsGeometry,
    QgsProject,
)

from .geoservices import GeoserviceError, fetch_json

API_URL = "https://api.gbif.org/v1/occurrence/search"
TIMEOUT = 90

# Longueur maximale du polygone en WKT. Le service accepte des URL longues,
# mais pas les serveurs intermediaires d'un reseau de collectivite.
WKT_MAX = 3000

# Tolerances de simplification essayees, en degres : de 10 m a 1 km environ.
TOLERANCES = (0.0001, 0.0003, 0.001, 0.003, 0.01)

# Especes comptees par groupe : au-dela, la facette serait tronquee.
FACET_LIMIT = 100000

# Requetes de front. Le GBIF repond 429 a une rafale de treize : deux a la
# fois passent, et le bloc reste de l'ordre de dix secondes.
WORKERS = 2

# Attentes avant de rejouer une requete refusee pour exces de debit.
RETRY_DELAYS = (4.0, 10.0)

# (cle, cle taxonomique GBIF, libelle). Les cles sont celles de l'arbre
# taxonomique du GBIF, verifiees sur son API : 6 Plantae, 5 Fungi,
# 216 Insecta, 367 Arachnida, 52 Mollusca, 229 Malacostraca,
# 204 Actinopterygii, 131 Amphibia, 358 Reptilia, 212 Aves, 359 Mammalia,
# 734 Chiroptera.
GROUPES = (
    ("plantes", 6, "Plantes"),
    ("champignons", 5, "Champignons"),
    ("insectes", 216, "Insectes"),
    ("arachnides", 367, "Araignées et arachnides"),
    ("mollusques", 52, "Mollusques"),
    ("crustaces", 229, "Crustacés (malacostracés)"),
    ("poissons", 204, "Poissons osseux"),
    ("amphibiens", 131, "Amphibiens"),
    ("reptiles", 358, "Reptiles"),
    ("oiseaux", 212, "Oiseaux"),
    ("mammiferes", 359, "Mammifères"),
    ("chiropteres", 734, "dont chauves-souris"),
)

SOURCE = ("GBIF — Global Biodiversity Information Facility, observations "
          "publiées (comptes seulement)")


class BiodiversityError(RuntimeError):
    """Le GBIF n'a pas pu etre interroge."""


def _wkt(basin):
    """Contour du bassin en WGS 84, assez court pour une URL."""
    transform = QgsCoordinateTransform(
        QgsCoordinateReferenceSystem("EPSG:2154"),
        QgsCoordinateReferenceSystem("EPSG:4326"),
        QgsProject.instance(),
    )
    shape = QgsGeometry(basin)
    shape.transform(transform)
    for tolerance in TOLERANCES:
        simple = shape.simplify(tolerance)
        if simple.isEmpty():
            continue
        # Le GBIF attend des anneaux exterieurs tournant dans le sens
        # inverse des aiguilles d'une montre.
        forcer = getattr(simple, "forcePolygonCounterClockwise", None)
        if forcer is not None:
            simple = forcer()
        text = simple.asWkt(5)
        if len(text) <= WKT_MAX:
            return text
    # En dernier recours, l'enveloppe convexe : elle deborde du bassin, ce
    # que la note du rapport dit, mais elle tient toujours.
    hull = shape.convexHull().simplify(0.001)
    return hull.asWkt(5)


def _count(wkt, taxon_key=None):
    """(observations, especes distinctes) pour un groupe, ou pour tous.

    Le GBIF refuse les rafales (HTTP 429) : une requete refusee attend et
    recommence, deux fois au plus, plutot que de faire perdre tout le bloc.
    """
    for delay in RETRY_DELAYS:
        try:
            return _count_once(wkt, taxon_key)
        except GeoserviceError as exc:
            if "429" not in str(exc):
                raise
            time.sleep(delay)
    return _count_once(wkt, taxon_key)


def _count_once(wkt, taxon_key=None):
    params = [
        ("geometry", wkt),
        ("limit", "0"),
        ("occurrenceStatus", "PRESENT"),
        ("hasGeospatialIssue", "false"),
        ("facet", "speciesKey"),
        ("facetLimit", str(FACET_LIMIT)),
    ]
    if taxon_key is not None:
        params.append(("taxonKey", str(taxon_key)))
    payload = fetch_json(API_URL + "?" + urllib.parse.urlencode(params),
                         timeout=TIMEOUT)
    facets = payload.get("facets") or []
    especes = len(facets[0].get("counts") or []) if facets else 0
    return payload.get("count") or 0, especes


def compute(basin, progress=None):
    """Observations et especes par grand groupe, toutes demandees de front."""
    if progress:
        progress("Biodiversité observée (GBIF)...")
    values = {"gbif": None, "erreurs": []}
    try:
        wkt = _wkt(basin)
        observations, especes = _count(wkt)
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            futures = [(key, label, pool.submit(_count, wkt, taxon))
                       for key, taxon, label in GROUPES]
            groupes = []
            for key, label, future in futures:
                nb_obs, nb_esp = future.result()
                groupes.append({"cle": key, "libelle": label,
                                "observations": nb_obs, "especes": nb_esp})
    except (GeoserviceError, BiodiversityError) as exc:
        values["erreurs"].append("Biodiversité (GBIF) : {0}".format(exc))
        return values
    values["gbif"] = {
        "observations": observations,
        "especes": especes,
        "groupes": groupes,
        "source": SOURCE,
    }
    return values
