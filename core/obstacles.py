# -*- coding: utf-8 -*-
"""Obstacles a l'ecoulement et sites hydrometriques du bassin.

Deux couches du Sandre, qui ne decrivent pas un milieu mais ce qu'on y a
construit et ce qu'on y mesure :

  ROE          referentiel des obstacles a l'ecoulement. Barrages, seuils,
               digues : ce qui fragmente le lineaire et explique un regime
               perturbe. Un bassin s'apprecie autant par ce qu'on y a mis en
               travers que par sa pente.
  SiteHydro    sites hydrometriques, c'est-a-dire les stations de jaugeage.
               Leur presence decide si le bassin dispose de debits mesures ou
               s'il faudra les reconstituer.

L'un se compte, l'autre se localise : ni l'un ni l'autre ne se cumulent en
surface, et c'est pourquoi ils vivent ici et non dans protected.

La hauteur de chute cumulee merite un mot. Ce n'est pas une denivelee : c'est
la somme des chutes franchies par un poisson qui remonterait tout le bassin,
et c'est a ce titre qu'elle renseigne sur la continuite ecologique.

Elle est reconstituee, et il faut le savoir pour s'en servir. Le referentiel
ne renseigne la hauteur exacte que sur une minorite d'ouvrages ; sur les
autres il ne donne qu'une classe, "De 1.5m a inferieure a 2m". Le milieu de
la classe est alors retenu, ce qui rend un ordre de grandeur et non une
mesure. Les ouvrages sans hauteur ni classe ne comptent pour rien : la somme
est donc un minorant, jamais un majorant.
"""

import re

from . import sandre

LAYER_ROE = "sa:ObstEcoul"
LAYER_HYDRO = "sa:SiteHydro"

# Etat de l'ouvrage. Seul "Existant" fait obstacle aujourd'hui : un ouvrage
# detruit reste au referentiel, et le compter comme les autres surestimerait
# la fragmentation du bassin.
STATE_EXISTING = "existant"

# Absence de dispositif de franchissement piscicole, telle que le Sandre la
# libelle. Le test porte sur le libelle et non sur le code : celui-ci vaut
# "0" pour l'absence, ce qui se confond trop facilement avec une valeur nulle.
NO_FISH_PASS = "absence"

# Plafond du releve detaille, ouvrages et stations confondus.
#
# Il etait a quarante quand le rapport tenait sur une page et tronquait sa
# liste ; il n'a plus a border la mise en page, qui pagine desormais ce qu'on
# lui donne. Ce qu'il borde encore est la memoire et la taille du fichier :
# un bassin de plusieurs centaines de kilometres carres peut porter plusieurs
# centaines d'ouvrages, et chacun devient une ligne dans la page comme dans
# le classeur. Cinq cents laisse passer tous les bassins observes en essai
# sans exposer a un rapport de cent pages.
MAX_DETAIL = 500

_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")


def _type_of(attributes):
    """Type d'ouvrage, tel que le service le nomme.

    Le libelle est absent de la quasi-totalite des entites, et la nomenclature
    Sandre des types d'ouvrage n'est pas servie par son API : on affiche alors
    le code brut plutot que de lui preter un sens. Un "1.1" dans le rapport se
    verifie ; un "Barrage" invente ne se verifie pas.
    """
    label = str(attributes.get("LbTypeOuvrage") or "").strip()
    if label:
        return label
    code = str(attributes.get("CdTypeOuvrage") or "").strip()
    return "Type Sandre {0}".format(code) if code else "Type non renseigné"


def _height_of(attributes):
    """Hauteur de chute en metres, et sa provenance.

    Renvoie (hauteur ou None, "mesuree" | "classe" | None). La hauteur exacte
    prime ; a defaut, le milieu de la classe libellee est retenu, et une
    classe ouverte - "superieure a 10m" - rend sa borne, qui la minore.
    """
    exact = sandre.as_float(attributes.get("HautChutEtObstEcoul"))
    if exact is not None and exact > 0:
        return exact, "mesuree"

    label = str(attributes.get("LbHautChutClObstEcoul") or "")
    bounds = [float(value.replace(",", "."))
              for value in _NUMBER.findall(label)]
    if not bounds:
        return None, None
    if len(bounds) >= 2:
        return (bounds[0] + bounds[1]) / 2.0, "classe"
    return bounds[0], "classe"


def _has_fish_pass(attributes):
    """L'ouvrage porte-t-il un dispositif de franchissement piscicole ?

    None quand le referentiel ne dit rien : sur ce sujet, l'absence
    d'information et l'absence de passe ne se confondent pas.
    """
    label = str(attributes.get("LbTypeDispFranchPiscicole1") or "").strip()
    if not label:
        return None
    return not label.lower().startswith(NO_FISH_PASS)


def _is_existing(attributes):
    state = str(attributes.get("LbEtOuvrage") or "").strip().lower()
    return state.startswith(STATE_EXISTING)


def obstacles(basin, linear_km=None, progress=None):
    """Obstacles a l'ecoulement recenses dans le bassin."""
    if progress:
        progress("Obstacles à l'écoulement (ROE)...")

    records = []
    for feature, geometry in sandre.features_in(LAYER_ROE, basin):
        attributes = sandre.attributes(feature)
        point = geometry.asPoint()
        height, origin = _height_of(attributes)
        records.append({
            "code": attributes.get("CdObstEcoul"),
            "nom": (attributes.get("NomPrincipalObstEcoul")
                    or attributes.get("NomSecondaireObstEcoul")),
            "type": _type_of(attributes),
            "etat": attributes.get("LbEtOuvrage"),
            "existant": _is_existing(attributes),
            "chute_m": height,
            "chute_origine": origin,
            "chute_classe": attributes.get("LbHautChutClObstEcoul"),
            "passe_a_poissons": _has_fish_pass(attributes),
            "usage": attributes.get("LbUsageObstEcoul1"),
            "grenelle": sandre.as_bool(attributes.get("GrenObstEcoul")),
            "cours_d_eau": attributes.get("NomEntiteHydrographique"),
            "x": point.x(),
            "y": point.y(),
        })

    heights = [r["chute_m"] for r in records if r["chute_m"]]
    existing = [r for r in records if r["existant"]]
    by_class = {}
    for record in records:
        label = record["chute_classe"] or "Hauteur non renseignée"
        by_class[label] = by_class.get(label, 0) + 1

    records.sort(key=lambda record: -(record["chute_m"] or 0.0))
    return {
        "nb": len(records),
        "nb_existants": len(existing),
        "nb_grenelle": sum(1 for r in records if r["grenelle"]),
        "nb_avec_passe": sum(1 for r in records if r["passe_a_poissons"]),
        "nb_sans_passe": sum(1 for r in records
                             if r["passe_a_poissons"] is False),
        "nb_chute_connue": len(heights),
        "chute_cumulee_m": sum(heights) if heights else None,
        "chute_max_m": max(heights) if heights else None,
        # La densite se rapporte au lineaire connu de la BD TOPO dans le
        # bassin, pas a sa surface : un obstacle barre un cours d'eau, il
        # n'occupe pas un territoire.
        "par_km": len(records) / linear_km if linear_km else None,
        # Repartition par classe de hauteur, seule nomenclature que le service
        # libelle lui-meme. Le type d'ouvrage n'arrive qu'en code brut.
        "par_classe": [{"classe": label, "nb": count}
                       for label, count in sorted(by_class.items(),
                                                  key=lambda kv: -kv[1])],
        "sites": records[:MAX_DETAIL],
        "source": "ROE — Référentiel des obstacles à l'écoulement (Sandre)",
    }


def gauging_sites(basin, progress=None):
    """Sites hydrometriques du Sandre situes dans le bassin."""
    if progress:
        progress("Sites hydrométriques...")

    records = []
    for feature, geometry in sandre.features_in(LAYER_HYDRO, basin):
        attributes = sandre.attributes(feature)
        point = geometry.asPoint()
        records.append({
            "code": attributes.get("CdSiteHydro"),
            "nom": (attributes.get("LbAffichageSiteHydro")
                    or attributes.get("LbSiteHydro")),
            "type": attributes.get("TypSiteHydro"),
            "gestionnaire": attributes.get("NomIntervenant"),
            "x": point.x(),
            "y": point.y(),
        })

    records.sort(key=lambda r: str(r["code"] or ""))
    return {
        "nb": len(records),
        "codes": ", ".join(r["code"] for r in records if r["code"]),
        "sites": records[:MAX_DETAIL],
        "source": "Sites hydrométriques (Sandre)",
    }


def compute(basin, linear_km=None, with_obstacles=True, with_gauges=True,
            progress=None):
    """Obstacles et stations du bassin.

    Une couche indisponible laisse sa partie a None sans faire echouer
    l'autre : le Sandre rend son service inegalement selon les heures, et un
    rapport ampute d'une ligne vaut mieux qu'un rapport non produit.
    """
    values = {"roe": None, "hydrometrie": None, "erreurs": []}
    if with_obstacles:
        try:
            values["roe"] = obstacles(basin, linear_km, progress)
        except RuntimeError as exc:
            values["erreurs"].append(
                "Obstacles à l'écoulement : {0}".format(exc))
    if with_gauges:
        try:
            values["hydrometrie"] = gauging_sites(basin, progress)
        except RuntimeError as exc:
            values["erreurs"].append("Sites hydrométriques : {0}".format(exc))
    return values
