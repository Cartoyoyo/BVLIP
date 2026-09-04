# -*- coding: utf-8 -*-
"""Enchainement complet du traitement, du point clique au bassin caracterise.

Ce module est le seul endroit ou l'ordre des etapes est ecrit. Le panneau et
l'algorithme Processing l'appellent tous les deux : une correction faite ici
profite aux deux points d'entree, et il devient impossible qu'ils divergent.

L'orchestration ne produit aucun fichier de sortie : elle renvoie les resultats
bruts, a charge de l'appelant de les ecrire en GeoPackage ou de les verser dans
un puits Processing.
"""

import os
import shutil
import tempfile
import time

from . import dem, delineation, landcover, metrics, network, waterbody
from .delineation import CONTAINMENT_MIN

# Etapes annoncees a la barre de progression. La liste sert aussi de contrat :
# une etape desactivee est comptee puis sautee, pour que l'avancement reste
# lineaire quelles que soient les options.
STEPS = (
    "emprise",
    "mnt",
    "delimitation",
    "affinage",
    "metriques",
    "masse_eau",
    "occupation_sol",
)

# Marge conservee de part et d'autre du bassin grossier lors du recadrage.
# Elle n'a qu'a absorber le deplacement du contour entre les deux mailles,
# soit une ou deux mailles grossieres : 50 m en represente deja cinq a une
# maille de 10 m. La prendre plus large ne rend rien plus sur et gonfle
# l'emprise, ce qui peut suffire a repasser au-dessus du plafond de memoire et
# a perdre le benefice du recadrage.
#
# Une marge serree n'est pas risquee pour autant : si le contour fin affleure
# le bord du recadrage, on le detecte et on recommence plus large.
REFINE_MARGIN = 50.0

# Facteur d'elargissement quand le contour fin affleure le bord du recadrage.
REFINE_MARGIN_GROWTH = 4.0

# Prefixe des repertoires de travail. Il sert aussi au balayage des oublis :
# tout ce qui le porte dans le temporaire du systeme nous appartient.
WORKDIR_PREFIX = "bvlip_"

# Age a partir duquel un repertoire de travail est repute abandonne. Aucun
# calcul ne dure six heures ; au-dela, c'est une session qui s'est terminee
# sans nettoyer - QGIS ferme brutalement, plugin recharge en cours de route.
# Le delai protege les autres instances de QGIS ouvertes en meme temps, dont
# on ne doit pas effacer le repertoire en cours d'utilisation.
WORKDIR_MAX_AGE_HOURS = 6

# Repertoires que le systeme n'a pas laisse effacer sur le coup.
#
# QGIS met en cache les connexions OGR : le GeoPackage de vectorisation reste
# ouvert un moment apres la destruction de la couche qui l'a lu, et Windows
# refuse alors d'effacer le fichier. Les gros fichiers - le MNT et les
# rasters d'ecoulement, de cinquante a trois cents megaoctets - partent bien ;
# il ne subsiste qu'un GeoPackage de deux cents kilooctets. On le reprend au
# calcul suivant, quand la connexion a ete relachee, plutot que d'attendre le
# balayage des six heures.
_PENDING = set()


class PipelineOptions:
    """Reglages du traitement, avec des valeurs par defaut utilisables telles
    quelles sur un bassin de quelques kilometres carres."""

    def __init__(self, snap_radius=50.0, thalweg_radius=50.0, resolution=None,
                 simplify_cells=2.0, stream_threshold=200,
                 with_metrics=True, with_water_body=True,
                 with_land_cover=True, water_body_details=False,
                 max_pixels=None, refine=False,
                 refine_margin=REFINE_MARGIN, workdir=None,
                 allow_oversize=False):
        self.snap_radius = snap_radius
        self.thalweg_radius = thalweg_radius
        # None : la maille s'ajuste a l'emprise et a la memoire disponible.
        self.resolution = resolution
        self.max_pixels = max_pixels
        # refine : seconde passe sur le bassin recadre, a maille plus fine.
        self.refine = refine
        self.refine_margin = refine_margin
        self.simplify_cells = simplify_cells
        self.stream_threshold = stream_threshold
        self.with_metrics = with_metrics
        self.with_water_body = with_water_body
        self.with_land_cover = with_land_cover
        self.water_body_details = water_body_details
        self.workdir = workdir
        # Leve le garde-fou d'emprise du reseau amont. Ne se met a True que
        # sur demande explicite : voir network.OversizeBasinError.
        self.allow_oversize = allow_oversize


def _discard(path):
    """Efface un repertoire de travail, ou le note pour plus tard."""
    shutil.rmtree(path, ignore_errors=True)
    if os.path.isdir(path):
        _PENDING.add(path)
    else:
        _PENDING.discard(path)


def sweep_workdirs(max_age_hours=WORKDIR_MAX_AGE_HOURS):
    """Efface les repertoires de travail abandonnes par des sessions passees.

    Le nettoyage de fin de calcul suffit tant que tout se passe bien ; il ne
    couvre pas la fermeture brutale de QGIS ni le rechargement du plugin en
    cours de traitement. Sans ce balayage, les oublis s'accumulent
    indefiniment - releve sur un poste : 116 repertoires et six gigaoctets,
    jusqu'a saturer le disque et faire echouer les calculs sur des rasters
    tronques, sans que rien ne relie la panne a sa cause.

    Renvoie le nombre de repertoires effaces.
    """
    root = tempfile.gettempdir()
    cutoff = time.time() - max_age_hours * 3600
    removed = 0
    try:
        names = os.listdir(root)
    except OSError:
        return 0
    for name in names:
        if not name.startswith(WORKDIR_PREFIX):
            continue
        path = os.path.join(root, name)
        try:
            if not os.path.isdir(path) or os.path.getmtime(path) > cutoff:
                continue
        except OSError:
            continue
        shutil.rmtree(path, ignore_errors=True)
        removed += 1
    return removed


def run(x, y, options=None, progress=None, feedback=None, cancelled=None,
        resume=None):
    """Delimite et caracterise le bassin versant draine par (x, y).

    Le repertoire de travail est cree ici et detruit en sortant, quel que
    soit le sort du calcul. Il pese de cinquante a trois cents megaoctets -
    le MNT et les rasters d'ecoulement - et rien ne le lit une fois la chaine
    terminee : les couches produites sont en memoire et le rapport
    reconstruit ce dont il a besoin. Un appelant qui fournit son propre
    repertoire en garde la charge.
    """
    for pending in list(_PENDING):
        _discard(pending)

    options = options or PipelineOptions()
    owned = options.workdir is None
    if owned:
        options.workdir = tempfile.mkdtemp(prefix=WORKDIR_PREFIX)
    try:
        return _run(x, y, options, progress, feedback, cancelled, resume)
    finally:
        if owned:
            _discard(options.workdir)
            options.workdir = None


def _run(x, y, options, progress, feedback, cancelled, resume):
    """Corps de la chaine, sur un repertoire de travail deja etabli.

    x et y sont en Lambert 93. progress recoit (indice d'etape, libelle) ;
    cancelled est un appelable renvoyant True pour interrompre proprement.

    resume reprend l'etat porte par une OversizeBasinError precedente, quand
    l'utilisateur a demande de poursuivre un calcul refuse : le chevelu deja
    charge n'est pas retelecharge.

    Renvoie un dictionnaire dont les cles reprennent les etapes : network,
    dem, delineation, metrics, water_body, land_cover.
    """
    workdir = options.workdir
    os.makedirs(workdir, exist_ok=True)

    def step(index, message):
        if progress is not None:
            progress(index, message)

    def stop():
        return cancelled is not None and cancelled()

    step(0, "Emprise de calcul et accrochage de l'exutoire")
    network_result = network.upstream_extent(
        x, y,
        snap_radius=options.snap_radius,
        progress=lambda m: step(0, m),
        allow_oversize=options.allow_oversize,
        resume=resume,
    )
    if stop():
        return None

    step(1, "Telechargement du MNT")
    dem_info = dem.download_dem(
        network_result["bbox"], os.path.join(workdir, "mnt.tif"),
        resolution=options.resolution,
        max_pixels=options.max_pixels,
        progress=lambda m: step(1, m),
    )
    if stop():
        return None

    step(2, "Delimitation du bassin")
    delineation_result = delineation.delineate(
        dem_info, network_result["outlet"], workdir,
        threshold=options.stream_threshold,
        snap_radius=options.thalweg_radius,
        simplify_cells=options.simplify_cells,
        upstream_km=_upstream_km(network_result),
        upstream=network_result.get("upstream"),
        validate=lambda geometry: network_containment(
            geometry, network_result.get("upstream"),
            (network_result.get("stream") or {}).get("cleabs"),
        ),
        progress=lambda m: step(2, m),
        feedback=feedback,
    )
    if stop():
        return None

    # Controle de coherence : le bassin doit contenir le reseau qu'il draine.
    upstream = network_result.get("upstream") or []
    containment = network_containment(
        delineation_result["geometry"], upstream,
        (network_result.get("stream") or {}).get("cleabs"),
    )
    delineation_result["part_reseau_dedans"] = containment
    if containment is not None:
        step(2, "Reseau strictement amont contenu dans le bassin : "
                "{0:.0f} %".format(100 * containment))
        if containment < CONTAINMENT_MIN:
            raise delineation.DelineationError(
                "Le bassin obtenu ne contient que {0:.0f} % du reseau "
                "hydrographique strictement a l'amont de l'exutoire : ce "
                "n'est pas le bassin de ce cours d'eau, l'exutoire est tombe "
                "sur un autre ecoulement. Elargissez le rayon de recalage sur "
                "le chevelu, ou deplacez le point.".format(100 * containment)
            )

    result = {
        "network": network_result,
        "dem": dem_info,
        "delineation": delineation_result,
        "metrics": None,
        "water_body": None,
        "land_cover": None,
        "avertissements": [],
        "affinage": None,
    }

    # Deux facons de rendre un bassin tronque sans que rien ne le signale.
    # Elles se ressemblent et n'ont pas la meme cause : la premiere vient du
    # reseau, la seconde du MNT. Aucune n'est rattrapable en aval, parce
    # qu'un bassin coupe garde l'allure d'un bassin juste - et que le
    # controle de contenance du reseau, calcule sur ce meme reseau tronque,
    # le valide au lieu de l'alerter.
    if network_result.get("truncated"):
        result["avertissements"].append(
            "Reseau amont incomplet : le plafond d'emprise a ete atteint "
            "avant d'avoir remonte tout le chevelu. Le bassin est tronque."
        )
    edge = _basin_on_edge(delineation_result["geometry"], dem_info)
    if edge:
        result["avertissements"].append(
            "Le contour du bassin affleure le bord du MNT sur {0} : il est "
            "coupe par l'emprise de calcul et non par la ligne de partage "
            "des eaux. La surface annoncee est un minorant.".format(edge)
        )

    if options.refine:
        step(3, "Recadrage et seconde passe")
        refined = _refine(
            network_result, dem_info, delineation_result, options, workdir,
            report=lambda m: step(3, m), feedback=feedback,
        )
        if refined is not None:
            result["dem"] = refined["dem"]
            result["delineation"] = refined["delineation"]
            result["affinage"] = refined["resume"]
            dem_info = refined["dem"]
            delineation_result = refined["delineation"]
        elif result["dem"]["resolution"] > dem.RESOLUTION_STEPS[0]:
            # Le message dit ce qui est constate, pas une cause supposee :
            # l'affinage renonce aussi bien faute de memoire que parce que le
            # recadrage ne fait pas gagner un cran de maille, et le journal
            # affichait alors un avertissement qui contredisait l'etape
            # elle-meme.
            result["avertissements"].append(
                "Affinage sans effet : meme recadre sur le bassin, le calcul "
                "ne descend pas sous la maille de {0:.0f} m.".format(
                    result["dem"]["resolution"])
            )
    if stop():
        return result

    # Les trois etapes suivantes sont de l'enrichissement : un service
    # indisponible ne doit pas faire perdre le bassin, deja calcule.
    if options.with_metrics:
        step(4, "Caracteristiques morphometriques")
        try:
            result["metrics"] = metrics.compute(
                delineation_result, network_result,
                progress=lambda m: step(4, m),
            )
        except Exception as exc:
            result["avertissements"].append(
                "Metriques non calculees : {0}".format(exc)
            )
    if stop():
        return result

    if options.with_water_body:
        step(5, "Masse d'eau DCE")
        try:
            result["water_body"] = waterbody.find_water_body(
                *delineation_result["outlet"],
                detailed=options.water_body_details,
            )
        except Exception as exc:
            result["avertissements"].append(
                "Masse d'eau non identifiee : {0}".format(exc)
            )
    if stop():
        return result

    if options.with_land_cover:
        step(6, "Occupation du sol")
        try:
            result["land_cover"] = landcover.compute(
                delineation_result["geometry"],
                progress=lambda m: step(6, m),
            )
        except Exception as exc:
            result["avertissements"].append(
                "Occupation du sol non etablie : {0}".format(exc)
            )

    return result


def _upstream_km(network_result):
    """Lineaire du reseau amont connu de la BD TOPO, en kilometres.

    Il borne le recalage de l'exutoire sur le talweg : voir
    delineation.snap_to_thalweg.
    """
    return sum(record["geometry"].length()
               for record in network_result.get("upstream") or ()) / 1000.0


def network_containment(basin_geometry, upstream, outlet_stream_id=None):
    """Part du reseau strictement amont contenue dans le bassin, entre 0 et 1.

    C'est le controle de coherence le plus parlant qui soit : un bassin
    versant contient necessairement les cours d'eau qu'il draine. Si le
    lineaire connu a l'amont de l'exutoire se retrouve en dehors du polygone,
    ce n'est pas le bassin cherche - l'exutoire est tombe sur un autre
    ecoulement.

    Le troncon qui porte l'exutoire est ecarte du calcul : il se prolonge vers
    l'aval au-dela du point de sortie, et cette partie-la est legitimement
    dehors. La mesurer brouillerait le signal - sur un cas d'essai, 78 % au
    lieu des 100 % que donnent les troncons strictement amont.

    Renvoie None quand il n'y a pas de troncon strictement amont, cas d'une
    tete de bassin : il n'y a alors rien a verifier de ce cote.
    """
    total = inside = 0.0
    for record in upstream or []:
        if outlet_stream_id is not None and record.get("id") == outlet_stream_id:
            continue
        geometry = record["geometry"]
        length = geometry.length()
        if length <= 0:
            continue
        total += length
        clipped = geometry.intersection(basin_geometry)
        if not clipped.isEmpty():
            inside += clipped.length()
    return (inside / total) if total > 0 else None




def _basin_bbox(geometry, margin):
    box = geometry.boundingBox()
    return (box.xMinimum() - margin, box.yMinimum() - margin,
            box.xMaximum() + margin, box.yMaximum() + margin)


def _basin_on_edge(geometry, dem_info, tolerance=None):
    """Cotes de l'emprise du MNT que le contour du bassin vient toucher.

    Renvoie une chaine listant les bords concernes, ou None. C'est le seul
    controle qui detecte une troncature venue du MNT : un bassin dont la
    ligne de partage des eaux est reelle s'arrete a distance du bord, un
    bassin coupe s'y colle sur toute la longueur.

    La tolerance vaut deux mailles par defaut : le contour simplifie peut
    s'ecarter d'une maille du bord sans que le bassin soit pour autant
    complet.
    """
    resolution = dem_info["resolution"]
    if tolerance is None:
        tolerance = 2 * resolution
    xmin, ymin, xmax, ymax = dem_info["bbox"]
    box = geometry.boundingBox()
    sides = []
    if box.xMinimum() - xmin < tolerance:
        sides.append("l'ouest")
    if box.yMinimum() - ymin < tolerance:
        sides.append("le sud")
    if xmax - box.xMaximum() < tolerance:
        sides.append("l'est")
    if ymax - box.yMaximum() < tolerance:
        sides.append("le nord")
    if not sides:
        return None
    if len(sides) < 2:
        return sides[0]
    return "{0} et {1}".format(", ".join(sides[:-1]), sides[-1])


def _touches(inner, outer, tolerance):
    """Le bassin obtenu affleure-t-il le bord de l'emprise recadree ?"""
    box = inner.boundingBox()
    return (box.xMinimum() - outer[0] < tolerance
            or box.yMinimum() - outer[1] < tolerance
            or outer[2] - box.xMaximum() < tolerance
            or outer[3] - box.yMaximum() < tolerance)


def _refine(network_result, coarse_dem, coarse_basin, options, workdir,
            report=None, feedback=None):
    """Seconde passe a maille plus fine, sur le bassin recadre.

    L'interet est celui-ci : l'emprise de la premiere passe est l'enveloppe du
    reseau amont elargie de deux kilometres, bien plus vaste que le bassin
    lui-meme. Une fois le bassin grossier connu, on peut recadrer dessus et
    consacrer la memoire economisee a une maille plus fine.

    Le resultat reste exact : le bassin fin est contenu dans le bassin
    grossier a une maille pres, donc les directions d'ecoulement calculees sur
    l'emprise recadree sont identiques a l'interieur. On le verifie apres coup,
    et on elargit la marge si le contour affleure le bord.

    Ce que l'affinage apporte, mesure sur un bassin de 146 km2 entre 10 m et
    5 m : la surface et les altitudes ne bougent pas, le plus long cheminement
    gagne 2,3 % et la pente moyenne 1,5 %. Le perimetre et l'indice de
    Gravelius, eux, dependent surtout de la tolerance de simplification et non
    de la maille : l'affinage ne les rend pas plus justes.

    Renvoie None si rien n'est a gagner ou si la seconde passe echoue : le
    resultat de la premiere passe reste alors valable.
    """
    def say(message):
        if report is not None:
            report(message)

    coarse_resolution = coarse_dem["resolution"]
    if coarse_resolution <= dem.RESOLUTION_STEPS[0]:
        say("Deja calcule a la maille la plus fine : rien a affiner.")
        return None

    # La marge demandee est respectee telle quelle. L'elargir ne pourrait pas
    # aider a gagner une maille plus fine, au contraire : une emprise plus
    # vaste demande plus de memoire. Elle n'est elargie que dans un cas, et
    # apres coup, si le contour fin affleure le bord.
    margin = max(2 * coarse_resolution, options.refine_margin)

    for attempt in range(2):
        bbox = _basin_bbox(coarse_basin["geometry"], margin)
        resolution, count, _ceiling = dem.choose_resolution(
            bbox, options.max_pixels
        )
        if resolution >= coarse_resolution:
            say("Le bassin recadre ne permet pas de descendre sous "
                "{0:.0f} m : affinage abandonne.".format(coarse_resolution))
            return None

        say("Recadrage sur le bassin ({0:.0f} km2 avec {1:.0f} m de marge) : "
            "maille ramenee de {2:.0f} m a {3:.0f} m ({4:.1f} Mpx).".format(
                (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]) / 1e6, margin,
                coarse_resolution, resolution, count / 1e6))

        folder = os.path.join(workdir, "affinage{0}".format(attempt))
        os.makedirs(folder, exist_ok=True)
        fine_dem = dem.download_dem(
            bbox, os.path.join(folder, "mnt.tif"),
            resolution=resolution, max_pixels=options.max_pixels,
            progress=say,
        )
        fine_basin = delineation.delineate(
            fine_dem, network_result["outlet"], folder,
            threshold=options.stream_threshold,
            snap_radius=options.thalweg_radius,
            simplify_cells=options.simplify_cells,
            upstream_km=_upstream_km(network_result),
            upstream=network_result.get("upstream"),
            validate=lambda geometry: network_containment(
                geometry, network_result.get("upstream"),
                (network_result.get("stream") or {}).get("cleabs"),
            ),
            progress=say, feedback=feedback,
        )

        if _touches(fine_basin["geometry"], bbox, 2 * resolution):
            # Le contour fin sort du recadrage : la premiere passe avait
            # sous-estime le bassin. On elargit et on recommence, une fois.
            say("Le contour affleure le bord du recadrage : marge elargie.")
            margin *= REFINE_MARGIN_GROWTH
            continue

        before = coarse_basin["area"] / 1e6
        after = fine_basin["area"] / 1e6
        say("Affinage : {0:.3f} km2 a {1:.0f} m, contre {2:.3f} km2 a "
            "{3:.0f} m ({4:+.2f} %).".format(
                after, resolution, before, coarse_resolution,
                100 * (after - before) / before if before else 0.0))
        return {
            "dem": fine_dem,
            "delineation": fine_basin,
            "resume": {
                "maille_initiale_m": coarse_resolution,
                "maille_finale_m": resolution,
                "surface_initiale_km2": before,
                "surface_finale_km2": after,
                "marge_m": margin,
            },
        }

    say("Affinage abandonne : le contour deborde encore apres elargissement.")
    return None


def summary(result):
    """Resume court du resultat, pour le journal de l'interface."""
    if not result:
        return "Traitement interrompu."
    delineated = result["delineation"]
    lines = [
        "Surface : {0:.4f} km2 ({1:.2f} ha)".format(
            delineated["area"] / 1e6, delineated["area"] / 1e4
        ),
        "Perimetre : {0:.0f} m".format(delineated["perimeter"]),
        "Exutoire : {0:.1f} ; {1:.1f}".format(*delineated["outlet"]),
    ]
    values = result.get("metrics")
    if values:
        lines.append("Gravelius : {0:.3f}".format(values["gravelius"]))
        lines.append("Pente moyenne : {0:.1f} %".format(
            values["pente_moyenne_pct"]))
        lines.append("Plus long cheminement : {0:.3f} km".format(
            values["long_cheminement_km"]))
    body = result.get("water_body")
    if body and body.get("code_eu"):
        lines.append("Masse d'eau : {0}".format(body["code_eu"]))
    cover = result.get("land_cover") or {}
    corine = cover.get("corine")
    if corine and corine.get("classes"):
        dominant = corine["classes"][0]
        lines.append("Occupation dominante : {0} ({1:.0f} %)".format(
            dominant["libelle"], dominant["part_pct"]))
    return "\n".join(lines)
