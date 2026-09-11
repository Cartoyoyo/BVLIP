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
import math
from concurrent.futures import ThreadPoolExecutor

from qgis.core import QgsGeometry, QgsJsonUtils, QgsPointXY

from .geoservices import (
    LAYER_STREAMS, LAYER_ZONES, WFS_MAX_FEATURES, wfs_features,
)

# Marge ajoutee autour du reseau amont : distance plausible entre un cours
# d'eau et la ligne de partage des eaux qui le domine.
DIVIDE_MARGIN = 2000.0

# Emprise de depart quand aucune zone hydrographique n'est trouvee.
DEFAULT_SEED = 5000.0

# Demi-cote de l'emprise de secours en mode "petit bassin versant" : le MNT
# telecharge couvre (2 * SMALL_BASIN_BUFFER) de large autour du point. Sans
# chevelu BD TOPO pour la dimensionner, on ne peut que parier large sans
# gaspiller : un kilometre suffit largement a un bassin de tete de bassin de
# quelques dizaines d'hectares a quelques km2, sans faire telecharger un MNT
# demesure pour un simple fosse.
SMALL_BASIN_BUFFER = 1000.0

# Garde-fou : nombre de troncons qu'on accepte de charger sans demander.
#
# Il porte sur ce qui est reellement lu, et non sur la taille d'une emprise.
# La difference n'est pas theorique : la densite du chevelu va du simple au
# double d'une region a l'autre, et un seuil en kilometres se trompait dans
# les deux sens - il refusait l'Allier a Vichy, qui se charge en 56 726
# troncons, et aurait laisse passer une emprise plus petite mais bien plus
# dense.
SEED_FEATURE_GUARD = 80000

# Plafond, quand l'utilisateur a demande d'aller au bout. Ces deux seuils
# sont les notres et protegent la memoire : le service, lui, pagine sans
# broncher au-dela - verifie sur une emprise de 267 185 troncons, servie
# jusqu'a la derniere page.
SEED_FEATURE_MAX = WFS_MAX_FEATURES

# Cote des dalles de chargement, en metres. Le chevelu se charge de proche en
# proche, une dalle a la fois, au lieu du rectangle qui l'englobe.
#
# Le compromis est celui-ci : une dalle plus fine epouse mieux le bassin mais
# multiplie les allers-retours, dont chacun coute sa seconde quelle que soit
# sa taille. A 10 km, une dalle porte quelques centaines de troncons en
# Auvergne, et les dalles contigues d'une meme rangee sont regroupees en une
# seule requete, ce qui rend le decoupage presque gratuit. Mesure sur l'Allier
# a Vichy : 125 dalles, 56 726 troncons lus pour 38 013 utiles, en 77 s. Le
# rectangle englobant en demandait 267 185 et n'aboutissait pas.
TILE_SIZE = 10000.0

# Tolerance pour decider qu'un point touche une limite de dalle. Un noeud pose
# exactement dessus appartient aux deux voisines.
TILE_EPSILON = 1.0

# Nombre maximal de vagues de chargement. Une vague avance d'une dalle le long
# du chevelu : vingt-trois suffisent a remonter l'Allier de Vichy a sa source,
# et la borne evite qu'une anomalie du graphe fasse tourner sans fin.
MAX_WAVES = 60

# Natures de troncons que la remontee du chevelu ne franchit pas.
#
# Un canal n'est pas un chemin de drainage : l'eau du Canal de Roanne a
# Digoin vient de la Loire par derivation, pas du ruissellement d'un bassin.
# La BD TOPO, elle, le relie au reste du reseau comme n'importe quel
# ecoulement, et la remontee l'empruntait. Trace relevee sur la Besbre a
# Diou, cinquante-trois troncons de long :
#
#     la Besbre -> Canal Lateral a la Loire (20 troncons)
#               -> Canal de Roanne a Digoin (25 troncons)
#               -> la Loire, et tout son bassin
#
# Le bassin de la Besbre fait un millier de kilometres carres ; la remontee
# en ramenait 47 442 troncons sur 16 100 km2, l'Arroux, le Sornin, le Rhins
# et la Bourbince compris. Aucun de ces cours d'eau ne s'ecoule vers
# l'exutoire.
#
# Ce qui reste franchissable, et doit le rester : les buses, sous lesquelles
# passent des ruisseaux ordinaires, les ecoulements canalises, qui sont des
# cours d'eau naturels dans un lit amenage, et les retenues, qui sont sur le
# cours d'eau lui-meme. Les couper amputerait des bassins parfaitement
# normaux.
IMPASSABLE_NATURES = frozenset((
    "canal",
    "aqueduc",
    "retenue-bassin portuaire",
))

# Requetes menees de front dans une vague. Les dalles d'une meme vague sont
# independantes : elles sont decidees ensemble, a partir du meme parcours du
# graphe, et aucune n'attend le resultat d'une autre. Seules les vagues sont
# sequentielles, chacune ayant besoin du graphe complete par la precedente.
#
# Mesure sur huit dalles jamais chargees : 3,8 s en file, 0,8 s a quatre
# fils, et 3,4 s contre 0,9 s en inversant l'ordre pour ecarter un biais de
# charge du serveur. On s'en tient a quatre : le gain plafonne ensuite, et il
# n'y a pas de raison de matraquer un service public gratuit.
FETCH_WORKERS = 4


class NetworkError(RuntimeError):
    """Le reseau hydrographique ne permet pas de traiter cet exutoire."""


class NoNetworkNearbyError(NetworkError):
    """Aucun cours d'eau BD TOPO n'est accessible autour du point.

    A la difference d'OversizeBasinError, ce n'est pas une question de
    budget : il n'y a simplement rien a accrocher, ce qui coupe court avant
    meme de savoir quelle emprise de MNT telecharger. C'est le lot frequent
    des tout petits bassins de tete de bassin versant, la ou la BD TOPO ne
    numerise ni fosse ni ruisseau intermittent.

    L'exception porte le point et le rayon essayes : de quoi laisser
    l'appelant proposer une emprise de secours (voir small_basin_extent)
    plutot que d'echouer sec.
    """

    def __init__(self, x, y, snap_radius, message=None):
        self.x = x
        self.y = y
        self.snap_radius = snap_radius
        super().__init__(message or (
            "Aucun cours d'eau BD TOPO a moins de {0:.0f} m du point."
        ).format(snap_radius))


class OversizeBasinError(NetworkError):
    """Le chevelu amont porte plus de troncons que le budget n'en charge.

    Levee au lieu de renvoyer un resultat tronque. C'est le point important :
    un bassin coupe au bord de l'emprise reste un polygone d'allure credible,
    que rien ne distingue d'un bassin juste - ni sa forme, ni la part du
    reseau amont qu'il contient, puisque ce reseau est tronque de la meme
    facon et valide donc le faux resultat. Le seul moment ou l'anomalie est
    visible est ici, et le seul moyen de ne pas la perdre est de refuser.

    L'exception porte de quoi presenter le choix a l'utilisateur, et surtout
    un chiffre mesure plutot qu'une largeur : ce qu'il faudrait charger,
    contre ce qu'on charge.
    """

    def __init__(self, feature_count, budget, scale, extent_km2,
                 upstream_count=0, upstream_km=0.0, zone_name=None,
                 stuck=False, state=None):
        self.feature_count = feature_count
        self.budget = budget
        self.scale = scale
        self.extent_km2 = extent_km2
        self.upstream_count = upstream_count
        self.upstream_km = upstream_km
        self.zone_name = zone_name
        # stuck distingue les deux refus, qui n'ont pas la meme cause et
        # n'appellent pas la meme lecture : une emprise de depart deja trop
        # grande, ou une emprise qui tenait mais qu'on ne peut plus elargir.
        self.stuck = stuck
        # Tout ce qui a deja ete charge et parcouru. Si l'utilisateur decide
        # de poursuivre, le calcul reprend la ou il s'est arrete au lieu de
        # retelecharger et de reparcourir ce qu'il connait deja.
        self.state = state
        if stuck:
            message = (
                "Bassin trop grand pour etre calcule : le chevelu continue "
                "au-dela de l'emprise interrogee, et la moindre emprise plus "
                "large porterait {0} troncons quand le traitement en charge "
                "{1} au plus. Le bassin rendu serait tronque.".format(
                    feature_count, budget)
            )
        else:
            message = (
                "Bassin trop grand pour etre calcule : l'emprise a "
                "interroger ({0}, {1:.0f} km2) porte {2} troncons, quand le "
                "traitement en charge {3} au plus.".format(
                    scale, extent_km2, feature_count, budget)
            )
        super().__init__(
            message + " Choisissez un exutoire plus en amont, ou demandez "
            "explicitement le calcul integral."
        )


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


def _ends(geometry):
    """Premier et dernier sommet de la ligne, dans l'ordre de numerisation.

    Le sens d'ecoulement de la BD TOPO se lit par rapport a cet ordre : en
    "Sens direct", le premier sommet est le point amont. C'est ce qui permet
    de savoir ou le chevelu continue sans jamais consulter un MNT.
    """
    polyline = geometry.asPolyline()
    if not polyline:
        parts = geometry.asMultiPolyline()
        if not parts:
            return None, None
        polyline = [point for part in parts for point in part]
    if len(polyline) < 2:
        return None, None
    return polyline[0], polyline[-1]


class HydroNetwork:
    """Graphe des troncons hydrographiques, alimente au fur et a mesure.

    Le graphe se remplit par ajouts successifs plutot qu'en une fois : c'est
    ce qui permet de suivre le chevelu de proche en proche au lieu de charger
    le rectangle qui l'englobe. Les doublons sont ecartes, un troncon a
    cheval sur deux dalles etant rendu par les deux.
    """

    def __init__(self, features=()):
        self.features = []
        self._by_id = {}
        self._by_downstream_node = {}
        self._undirected = {}
        self.add(features)

    def add(self, features):
        """Ajoute des troncons au graphe. Renvoie le nombre de nouveaux."""
        added = 0
        for feature in features:
            properties = feature["properties"]
            key = properties.get("cleabs")
            if key is not None and key in self._by_id:
                continue
            geometry = _geometry(feature)
            if geometry.isEmpty():
                continue
            upstream, downstream = _endpoints(properties)
            first, last = _ends(geometry)
            record = {
                "id": key,
                "geometry": geometry,
                "properties": properties,
                "upstream_node": upstream,
                "downstream_node": downstream,
                # Ouvrage de transfert, qui ne draine pas de bassin : voir
                # IMPASSABLE_NATURES.
                "artificial": (properties.get("nature") or "").strip().lower()
                in IMPASSABLE_NATURES,
                # Position du sommet amont : c'est la que le chevelu
                # continue, et donc la qu'il faut aller chercher la suite.
                "upstream_point": (
                    last if upstream is not None
                    and upstream == _single(properties.get(
                        "lien_vers_noeud_hydrographique_fin"))
                    else first
                ),
            }
            self.features.append(record)
            if key is not None:
                self._by_id[key] = record
            added += 1
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
        return added

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

    def _inflows(self, node):
        """Troncons qui arrivent au noeud donne, orientes ou non.

        Les ouvrages de transfert sont ecartes : ils arrivent bien au noeud,
        mais ils n'y amenent pas le ruissellement d'un bassin. Les suivre
        ferait sortir du bassin cherche pour entrer dans celui qui alimente
        l'ouvrage - voir IMPASSABLE_NATURES.
        """
        return [record
                for record in (self._by_downstream_node.get(node, [])
                               + self._undirected.get(node, []))
                if not record["artificial"]]

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
                candidates.extend(self._inflows(node))
            else:
                for endpoint in ("lien_vers_noeud_hydrographique_ini",
                                 "lien_vers_noeud_hydrographique_fin"):
                    other = _single(current["properties"].get(endpoint))
                    if other is not None:
                        candidates.extend(self._inflows(other))
            for candidate in candidates:
                if candidate["id"] not in collected:
                    queue.append(candidate)
        return list(collected.values())

    def dead_ends(self, records):
        """Points amont des troncons dont l'amont n'est pas connu du graphe.

        Un noeud sans troncon entrant est soit une vraie source, soit un
        endroit ou le chargement s'arrete. Les deux se ressemblent ici et se
        departagent dehors, en regardant si le point tombe dans une dalle
        deja chargee : dans ce cas la suite aurait ete chargee avec, donc
        c'est une source.
        """
        points = []
        for record in records:
            node = record["upstream_node"]
            if node is None:
                continue
            others = [other for other in self._inflows(node)
                      if other["id"] != record["id"]]
            if others:
                continue
            point = record.get("upstream_point")
            if point is not None:
                points.append(point)
        return points


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


def _union(first, second):
    return (min(first[0], second[0]), min(first[1], second[1]),
            max(first[2], second[2]), max(first[3], second[3]))


def _tile_key(x, y):
    return (int(math.floor(x / TILE_SIZE)), int(math.floor(y / TILE_SIZE)))


def _tile_bbox(key):
    col, row = key
    return (col * TILE_SIZE, row * TILE_SIZE,
            (col + 1) * TILE_SIZE, (row + 1) * TILE_SIZE)


def _tiles_at(point, epsilon=TILE_EPSILON):
    """Dalles qu'un point touche, bord compris.

    Un point pose exactement sur une limite appartient aux deux dalles
    voisines. On les rend toutes, sinon un troncon qui repart de ce point
    pourrait n'etre servi que par celle qu'on n'a pas chargee.
    """
    x, y = point.x(), point.y()
    keys = set()
    for dx in (-epsilon, epsilon):
        for dy in (-epsilon, epsilon):
            keys.add(_tile_key(x + dx, y + dy))
    return keys


def _tiles_covering(bbox):
    """Toutes les dalles qui recouvrent une emprise."""
    first = _tile_key(bbox[0], bbox[1])
    last = _tile_key(bbox[2], bbox[3])
    return {(col, row)
            for col in range(first[0], last[0] + 1)
            for row in range(first[1], last[1] + 1)}


def _merge_runs(keys):
    """Regroupe des dalles contigues d'une meme rangee en une seule emprise.

    Chaque requete coute son aller-retour, quelle que soit sa taille. Vingt
    dalles alignees demandees separement coutent vingt fois cet aller-retour ;
    demandees d'un bloc, une seule fois, pour exactement les memes donnees.
    On ne regroupe que ce qui est reellement contigu : le bloc ne couvre alors
    rien de plus que les dalles qu'il remplace.
    """
    runs = []
    for row in sorted({row for _col, row in keys}):
        cols = sorted(col for col, other in keys if other == row)
        start = previous = cols[0]
        for col in cols[1:] + [None]:
            if col == previous + 1:
                previous = col
                continue
            runs.append((_union(_tile_bbox((start, row)),
                                _tile_bbox((previous, row))),
                         previous - start + 1))
            if col is not None:
                start = previous = col
    return runs


def upstream_extent(x, y, snap_radius=50.0, margin=DIVIDE_MARGIN,
                    progress=None, allow_oversize=False, resume=None):
    """Determine l'emprise de calcul et l'exutoire accroche.

    Le principe tient en une phrase : on accroche le point sur le premier
    troncon, on remonte le chevelu, et l'enveloppe de ce chevelu donne
    l'emprise du MNT. L'amont se lit dans les attributs de la BD TOPO -
    "sens_de_l_ecoulement" et les liens vers les noeuds - sans qu'aucun MNT
    soit necessaire pour le savoir.

    Reste a avoir le chevelu en memoire, et le WFS ne filtre que par emprise :
    on ne peut pas lui demander les troncons connectes a celui-ci. Plutot que
    de charger le rectangle qui englobe tout, on avance par dalles le long du
    chevelu. On charge la dalle du point, on remonte tant qu'on peut, et la ou
    le parcours bute sur un noeud sans amont connu, on charge la dalle qui
    contient ce noeud. Le graphe se propage ainsi le long des cours d'eau et
    ne couvre jamais que le bassin, la ou le rectangle englobant en couvrait
    trois a quatre fois trop.

    Un noeud sans troncon entrant est soit une vraie source, soit une limite
    de chargement. On les departage par un invariant : le WFS rend toute
    entite qui intersecte l'emprise demandee, donc un troncon qui repart d'un
    noeud interieur a une dalle chargee a forcement ete rendu avec elle. Un
    noeud interieur sans amont est donc une source, et lui seul.

    allow_oversize releve le budget de troncons. A ne mettre a True que sur
    demande explicite de l'utilisateur, prevenu de ce qu'il declenche.

    resume reprend l'etat porte par une OversizeBasinError precedente : les
    dalles deja chargees, le graphe deja construit et l'exutoire deja
    accroche. Poursuivre coute alors le seul chemin qui restait a faire,
    quand repartir de zero refaisait tout le trajet.

    Renvoie un dictionnaire :
        bbox           emprise a telecharger, en Lambert 93
        outlet         exutoire accroche (x, y)
        snap_distance  distance entre le point clique et le reseau
        stream         proprietes du troncon accroche
        upstream       liste des troncons amont
        zone           proprietes de la zone hydrographique, ou None
        iterations     nombre de vagues de chargement
        dalles         nombre de dalles chargees
        charges        nombre de troncons charges en tout
        truncated      present et vrai si le chevelu reste incomplet

    Leve OversizeBasinError quand le budget est atteint.
    """
    def report(message):
        if progress is not None:
            progress(message)

    budget = SEED_FEATURE_MAX if allow_oversize else SEED_FEATURE_GUARD

    if resume is not None:
        network = resume["network"]
        loaded = resume["loaded"]
        zone = resume["zone"]
        record = resume["record"]
        distance = resume["distance"]
        snapped = resume["snapped"]
        report("Reprise : {0} dalles et {1} troncons deja en memoire.".format(
            len(loaded), len(network)))
    else:
        network = HydroNetwork()
        loaded = set()
        record = distance = snapped = None
        seed, zone = seed_extent(x, y)
        report("Zone hydrographique : {0}".format(
            (zone or {}).get("toponyme") or "non identifiee"))

    def fetch(keys):
        """Charge les dalles demandees, en groupant ce qui est contigu.

        Les requetes d'une meme vague partent de front : elles ne dependent
        pas les unes des autres. Le graphe, lui, n'est alimente que dans le
        fil appelant, une fois les reponses la - il n'est pas fait pour etre
        ecrit a plusieurs.
        """
        runs = _merge_runs(keys)
        if not runs:
            # Rien a charger : toutes les dalles demandees sont deja la. Sans
            # ce garde, on demandait un pool de zero fil, ce qui leve une
            # ValueError au lieu de ne rien faire.
            return 0
        if len(runs) == 1:
            pages = [wfs_features(LAYER_STREAMS, bbox=runs[0][0])]
        else:
            with ThreadPoolExecutor(
                max_workers=min(FETCH_WORKERS, len(runs))
            ) as pool:
                pages = list(pool.map(
                    lambda run: wfs_features(LAYER_STREAMS, bbox=run[0]), runs
                ))
        fresh = 0
        for (bbox, _count), page in zip(runs, pages):
            fresh += network.add(page)
            loaded.update(_tiles_covering(bbox) & keys)
        return fresh

    def refuse(reason):
        raise OversizeBasinError(
            feature_count=len(network), budget=budget, scale=reason,
            extent_km2=len(loaded) * (TILE_SIZE / 1000.0) ** 2,
            upstream_count=len(upstream),
            upstream_km=sum(r["geometry"].length() for r in upstream) / 1000.0,
            zone_name=(zone or {}).get("toponyme"),
            state={
                "network": network, "loaded": loaded, "zone": zone,
                "record": record, "distance": distance, "snapped": snapped,
                "outlet": (x, y),
            },
        )

    # Premiere vague : de quoi trouver le troncon d'accrochage. On part des
    # dalles qui couvrent le rayon d'accrochage, et non de la zone
    # hydrographique entiere : le reste viendra en suivant le chevelu.
    upstream = []
    if record is None:
        wave = _tiles_covering((x - snap_radius, y - snap_radius,
                                x + snap_radius, y + snap_radius))
        fetch(wave)
        if not len(network):
            # Point loin de tout : on elargit une fois sur la zone
            # hydrographique, emprise de depart bien dimensionnee.
            fetch(_tiles_covering(seed) - loaded)
        if not len(network):
            raise NoNetworkNearbyError(x, y, snap_radius)

        found = network.nearest(x, y, snap_radius)
        if found is None:
            raise NoNetworkNearbyError(x, y, snap_radius)
        record, distance, snapped = found

    iterations = 0
    truncated = False
    for iterations in range(1, MAX_WAVES + 1):
        upstream = network.upstream_of(record)

        # La ou le parcours bute sans etre dans une dalle chargee, le chevelu
        # continue : c'est exactement la qu'il faut aller chercher la suite.
        wave = set()
        for point in network.dead_ends(upstream):
            wave |= _tiles_at(point) - loaded
        if not wave:
            break

        if len(network) >= budget:
            if not allow_oversize:
                refuse("chevelu en cours de remontee")
            report("Budget de {0} troncons atteint : chevelu "
                   "incomplet.".format(budget))
            truncated = True
            break

        report("Vague {0} : {1} dalle(s) a charger, {2} troncons amont "
               "connus".format(iterations, len(wave), len(upstream)))
        fetch(wave)
        report("  {0} dalles chargees, {1} troncons en memoire".format(
            len(loaded), len(network)))
    else:
        truncated = True
        report("Nombre de vagues epuise : chevelu incomplet.")

    if truncated and not allow_oversize:
        refuse("chevelu incomplet")

    upstream = network.upstream_of(record)
    report("Chevelu amont : {0} troncons, {1} dalles chargees, {2} troncons "
           "lus en tout".format(len(upstream), len(loaded), len(network)))

    result = {
        "bbox": _bbox_of(upstream, margin),
        "outlet": snapped,
        "snap_distance": distance,
        "stream": record["properties"],
        "upstream": upstream,
        "zone": zone,
        "iterations": iterations,
        "dalles": len(loaded),
        "charges": len(network),
    }
    if truncated:
        result["truncated"] = True
    return result


def small_basin_extent(x, y, buffer_m=SMALL_BASIN_BUFFER):
    """Emprise de secours quand aucun cours d'eau BD TOPO n'est accessible.

    C'est le lot des tout petits bassins de tete de bassin versant : la
    BD TOPO n'y numerise souvent ni fosse ni ruisseau intermittent, si bien
    qu'upstream_extent n'a rien ou aucun troncon a portee du rayon
    d'accrochage (voir NoNetworkNearbyError). Sans chevelu, il n'y a plus
    moyen de deduire l'emprise a telecharger du reseau amont : on se rabat
    sur un simple carre autour du point clicque.
    Cela laisse deux consequences assumees, non rattrapables ici : le
    recalage de l'exutoire (delineation.snap_to_thalweg) ne dispose plus du
    filtre par lineaire BD TOPO qui ecarte les petits chenaux errones, et
    aucun controle de coherence n'est possible en aval puisqu'il n'y a pas
    de reseau amont a comparer au bassin obtenu - exactement comme pour une
    tete de bassin ordinaire, ou ce controle ne dit deja rien.

    Renvoie un dictionnaire de meme forme qu'upstream_extent : bbox, outlet
    (le point clicque, non recale), et upstream vide.
    """
    return {
        "bbox": (x - buffer_m, y - buffer_m, x + buffer_m, y + buffer_m),
        "outlet": (x, y),
        "snap_distance": None,
        "stream": None,
        "upstream": [],
        "zone": None,
        "iterations": 0,
        "dalles": 0,
        "charges": 0,
        "small_basin": True,
    }
