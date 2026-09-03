# -*- coding: utf-8 -*-
"""Reseau hydrographique BD TOPO : accrochage de l'exutoire et remontee amont.

C'est ce module qui repond a la question "de quelle surface ai-je besoin ?"
avant de telecharger le moindre pixel de MNT. Plutot que de deviner un rayon,
on remonte le graphe des troncons a partir de l'exutoire : l'enveloppe du
reseau amont, elargie d'une marge, borne le bassin versant a coup sur, puisque
toute maille du bassin s'ecoule vers un de ces troncons.

Le graphe est construit en memoire a partir d'un seul appel WFS, puis parcouru
localement : pas de requete par noeud.
"""

import json

from qgis.core import QgsGeometry, QgsJsonUtils, QgsPointXY

from .geoservices import LAYER_STREAMS, LAYER_ZONES, wfs_features

# Marge ajoutee autour du reseau amont : distance plausible entre un cours
# d'eau et la ligne de partage des eaux qui le domine.
DIVIDE_MARGIN = 2000.0

# Emprise de depart quand aucune zone hydrographique n'est trouvee.
DEFAULT_SEED = 5000.0

MAX_SEED = 60000.0  # garde-fou : au-dela, on refuse plutot que de saturer


class NetworkError(RuntimeError):
    """Le reseau hydrographique ne permet pas de traiter cet exutoire."""


def _geometry(feature):
    """Convertit la geometrie GeoJSON d'une entite WFS en QgsGeometry."""
    return QgsGeometry(
        QgsJsonUtils.geometryFromGeoJson(json.dumps(feature["geometry"]))
    )


def _single(value):
    """Les liens BD TOPO sont tantot une chaine, tantot une liste."""
    if isinstance(value, (list, tuple)):
        return value[0] if value else None
    return value


def _endpoints(properties):
    """Renvoie (noeud amont, noeud aval) en tenant compte du sens d'ecoulement.

    Un troncon au sens indetermine (plan d'eau, bras artificiel) est renvoye
    sans orientation : il sera traite comme franchissable dans les deux sens,
    ce qui evite de couper le reseau au milieu d'un etang.
    """
    ini = _single(properties.get("lien_vers_noeud_hydrographique_ini"))
    fin = _single(properties.get("lien_vers_noeud_hydrographique_fin"))
    sens = (properties.get("sens_de_l_ecoulement") or "").lower()
    if "inverse" in sens:
        return fin, ini
    if "direct" in sens:
        return ini, fin
    return None, None  # sens inconnu : les deux extremites sont ouvertes


class HydroNetwork:
    """Graphe des troncons hydrographiques sur une emprise donnee."""

    def __init__(self, features):
        self.features = []
        self._by_downstream_node = {}
        self._undirected = {}
        for feature in features:
            geometry = _geometry(feature)
            if geometry.isEmpty():
                continue
            properties = feature["properties"]
            upstream, downstream = _endpoints(properties)
            record = {
                "id": properties.get("cleabs"),
                "geometry": geometry,
                "properties": properties,
                "upstream_node": upstream,
                "downstream_node": downstream,
            }
            self.features.append(record)
            if downstream is not None:
                self._by_downstream_node.setdefault(downstream, []).append(record)
            else:
                # Troncon non oriente : accessible par ses deux extremites.
                for node in (
                    _single(properties.get("lien_vers_noeud_hydrographique_ini")),
                    _single(properties.get("lien_vers_noeud_hydrographique_fin")),
                ):
                    if node is not None:
                        self._undirected.setdefault(node, []).append(record)

    def __len__(self):
        return len(self.features)

    def nearest(self, x, y, max_distance):
        """Troncon le plus proche du point, dans la limite donnee.

        Renvoie (enregistrement, distance, point accroche) ou None.
        """
        point = QgsGeometry.fromPointXY(QgsPointXY(x, y))
        best = None
        for record in self.features:
            distance = record["geometry"].distance(point)
            if best is None or distance < best[1]:
                best = (record, distance)
        if best is None or best[1] > max_distance:
            return None
        record, distance = best
        snapped = record["geometry"].nearestPoint(point).asPoint()
        return record, distance, (snapped.x(), snapped.y())

    def upstream_of(self, record):
        """Tous les troncons situes a l'amont du troncon donne, lui compris.

        Parcours en largeur du graphe inverse. Les troncons non orientes sont
        traverses une seule fois, ce qui suffit a franchir un plan d'eau sans
        risquer de boucler.
        """
        collected = {}
        queue = [record]
        while queue:
            current = queue.pop()
            key = current["id"]
            if key in collected:
                continue
            collected[key] = current
            node = current["upstream_node"]
            candidates = []
            if node is not None:
                candidates.extend(self._by_downstream_node.get(node, []))
                candidates.extend(self._undirected.get(node, []))
            else:
                for endpoint in ("lien_vers_noeud_hydrographique_ini",
                                 "lien_vers_noeud_hydrographique_fin"):
                    other = _single(current["properties"].get(endpoint))
                    if other is not None:
                        candidates.extend(self._by_downstream_node.get(other, []))
            for candidate in candidates:
                if candidate["id"] not in collected:
                    queue.append(candidate)
        return list(collected.values())


def _bbox_of(records, margin):
    """Enveloppe des troncons, elargie de la marge donnee.

    Les extremes sont suivis a la main plutot que par accumulation dans un
    QgsRectangle : cela evite d'avoir a partir d'un rectangle nul, dont la
    facon de le construire a change d'une version de QGIS a l'autre.
    """
    bounds = None
    for record in records:
        box = record["geometry"].boundingBox()
        if bounds is None:
            bounds = [box.xMinimum(), box.yMinimum(),
                      box.xMaximum(), box.yMaximum()]
            continue
        bounds[0] = min(bounds[0], box.xMinimum())
        bounds[1] = min(bounds[1], box.yMinimum())
        bounds[2] = max(bounds[2], box.xMaximum())
        bounds[3] = max(bounds[3], box.yMaximum())
    if bounds is None:
        raise NetworkError("Aucun troncon amont a delimiter.")
    return (bounds[0] - margin, bounds[1] - margin,
            bounds[2] + margin, bounds[3] + margin)


def _touches_border(records, bbox, tolerance):
    """Le reseau amont bute-t-il sur le bord de l'emprise interrogee ?

    Si oui, le graphe est tronque : des affluents existent au-dela et
    l'emprise doit etre elargie.
    """
    xmin, ymin, xmax, ymax = bbox
    for record in records:
        box = record["geometry"].boundingBox()
        if (box.xMinimum() - xmin < tolerance
                or box.yMinimum() - ymin < tolerance
                or xmax - box.xMaximum() < tolerance
                or ymax - box.yMaximum() < tolerance):
            return True
    return False


def seed_extent(x, y):
    """Premiere emprise de travail, calee sur la zone hydrographique du point.

    La zone hydrographique BD TOPO (heritee de la BD Carthage) est une unite
    coherente : elle donne une emprise de depart bien mieux dimensionnee qu'un
    rayon arbitraire. A defaut, on retombe sur un carre de 5 km.
    """
    probe = (x - 10, y - 10, x + 10, y + 10)
    features = wfs_features(LAYER_ZONES, bbox=probe)
    point = QgsGeometry.fromPointXY(QgsPointXY(x, y))
    for feature in features:
        geometry = _geometry(feature)
        if geometry.contains(point):
            box = geometry.boundingBox()
            box.grow(DIVIDE_MARGIN)
            return ((box.xMinimum(), box.yMinimum(),
                     box.xMaximum(), box.yMaximum()),
                    feature["properties"])
    return ((x - DEFAULT_SEED, y - DEFAULT_SEED,
             x + DEFAULT_SEED, y + DEFAULT_SEED), None)


def upstream_extent(x, y, snap_radius=50.0, margin=DIVIDE_MARGIN,
                    progress=None):
    """Determine l'emprise de calcul et l'exutoire accroche.

    Renvoie un dictionnaire :
        bbox           emprise a telecharger, en Lambert 93
        outlet         exutoire accroche (x, y)
        snap_distance  distance entre le point clique et le reseau
        stream         proprietes du troncon accroche
        upstream       liste des troncons amont
        zone           proprietes de la zone hydrographique, ou None
        iterations     nombre d'elargissements effectues
    """
    def report(message):
        if progress is not None:
            progress(message)

    bbox, zone = seed_extent(x, y)
    report("Zone hydrographique : {0}".format(
        (zone or {}).get("toponyme", "non identifiee")))

    iterations = 0
    while True:
        iterations += 1
        features = wfs_features(LAYER_STREAMS, bbox=bbox)
        network = HydroNetwork(features)
        report("Reseau charge : {0} troncons".format(len(network)))
        if not len(network):
            raise NetworkError(
                "Aucun troncon hydrographique dans l'emprise interrogee."
            )

        found = network.nearest(x, y, snap_radius)
        if found is None:
            raise NetworkError(
                "Aucun cours d'eau a moins de {0:.0f} m du point. Rapprochez "
                "l'exutoire du reseau ou augmentez le rayon "
                "d'accrochage.".format(snap_radius)
            )
        record, distance, snapped = found

        upstream = network.upstream_of(record)
        report("Troncons amont : {0}".format(len(upstream)))

        extent = _bbox_of(upstream, margin)
        if not _touches_border(upstream, bbox, margin * 0.5):
            return {
                "bbox": extent,
                "outlet": snapped,
                "snap_distance": distance,
                "stream": record["properties"],
                "upstream": upstream,
                "zone": zone,
                "iterations": iterations,
            }

        # Le reseau amont sort de l'emprise interrogee : on elargit.
        width = max(bbox[2] - bbox[0], bbox[3] - bbox[1])
        if width >= MAX_SEED:
            report("Emprise maximale atteinte, resultat possiblement tronque.")
            return {
                "bbox": extent,
                "outlet": snapped,
                "snap_distance": distance,
                "stream": record["properties"],
                "upstream": upstream,
                "zone": zone,
                "iterations": iterations,
                "truncated": True,
            }
        grow = width * 0.5
        bbox = (bbox[0] - grow, bbox[1] - grow, bbox[2] + grow, bbox[3] + grow)
        report("Elargissement de l'emprise a {0:.0f} km".format(
            (bbox[2] - bbox[0]) / 1000.0))
