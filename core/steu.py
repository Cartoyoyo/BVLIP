# -*- coding: utf-8 -*-
"""Stations de traitement des eaux usees du bassin, et leurs normes de rejet.

La couche du Sandre sa:SysTraitementEauxUsees recense les STEU de France
entiere. Elle donne ce qui interesse un diagnostic de bassin versant : ou
sont les rejets domestiques, quelle charge ils representent, et si
l'exploitant surveille ce qu'il rejette.

Elle ne donne pas les normes de rejet. Celles-ci n'existent nulle part en
donnee ouverte station par station : les valeurs opposables figurent dans
l'arrete prefectoral de chaque ouvrage, en PDF. Ce qui existe, en revanche,
c'est la regle qui les fixe - l'arrete du 21 juillet 2015 - et elle ne
depend que de deux choses : la capacite de la station en equivalent-habitants
et le fait de rejeter ou non en zone sensible a l'eutrophisation. Or ces deux
entrees sont dans la couche.

Les normes sont donc calculees ici, et non rapatriees. La nuance doit rester
lisible pour qui consulte la couche : ce sont les seuils reglementaires
applicables a la classe de la station, un plancher national. L'arrete
prefectoral peut etre plus strict, jamais plus permissif. Les champs le
disent dans leur intitule, et norme_source porte la reference du texte.

Un mot sur ce qui n'est pas la. Les mesures d'autosurveillance - ce que la
station rejette reellement, mois par mois - transitent par MesureSTEP, qui
est un logiciel de saisie pour les exploitants, pas un service consultable.
Elles remontent ensuite aux agences de l'eau, dont une seule les publie en
donnee ouverte a ce jour. Le seul indicateur de charge reelle disponible
partout est SomChrgMaxEntree, la charge maximale entrante, renseignee sur un
peu plus de la moitie des stations : rapportee a la capacite nominale, elle
donne le taux de charge, qui dit si l'ouvrage est sature.
"""

from . import sandre

LAYER_STEU = "sa:SysTraitementEauxUsees"

# Plafond du releve detaille, comme pour les obstacles : un bassin peut
# porter beaucoup de petites stations, et chacune devient une ligne dans le
# rapport comme dans le classeur.
MAX_DETAIL = 500

# Classes de capacite de l'arrete du 21 juillet 2015, converties en
# equivalent-habitants. Le texte raisonne en charge brute de DBO5 ; la
# conversion reglementaire est 1 EH = 60 g de DBO5 par jour, si bien que
# 120 kg/j valent 2 000 EH, 600 kg/j 10 000 EH et 6 000 kg/j 100 000 EH.
SEUIL_ERU_EH = 2000
SEUIL_NUTRIMENTS_EH = 10000
SEUIL_NUTRIMENTS_HAUT_EH = 100000

# Tableau 6 de l'annexe III : (concentration maximale en mg/L, rendement
# minimal en %). La concentration OU le rendement suffit - le texte les pose
# en alternative, pas en cumul. None signale un seuil que le tableau ne fixe
# pas : sous 2 000 EH, les MES ne sont tenues qu'a un rendement.
NORMES_DBO5 = {"petite": (35.0, 60.0), "grande": (25.0, 80.0)}
NORMES_DCO = {"petite": (200.0, 60.0), "grande": (125.0, 75.0)}
NORMES_MES = {"petite": (None, 50.0), "grande": (35.0, 90.0)}

# Tableau 7 : azote et phosphore, exiges des seules stations qui rejettent en
# zone sensible a l'eutrophisation, au-dela de 10 000 EH.
NORMES_NGL = {"moyenne": (15.0, 70.0), "haute": (10.0, 70.0)}
NORMES_PT = {"moyenne": (2.0, 80.0), "haute": (1.0, 80.0)}

NORME_SOURCE = ("Seuils réglementaires applicables — arrêté du 21 juillet "
                "2015, annexe III (l'arrêté préfectoral de la station peut "
                "être plus strict)")

# Prefixe du code de zone sensible qui signale justement l'absence de zone.
# Verifie sur le service : les stations hors zone sensible portent toutes
# FRHZS_00000, les autres un code de zone reelle et son nom.
HORS_ZONE_SENSIBLE = "FRHZS"


def _capacity(attributes):
    """Capacite nominale en EH, ou None si le referentiel ne la donne pas.

    Zero n'est pas une capacite : c'est ainsi que le service note l'absence
    de donnee, et une station a zero EH n'existerait pas. La traiter comme
    une valeur ferait tomber la station dans la classe des moins de 2 000 EH
    et lui inventerait des normes.
    """
    value = sandre.as_float(attributes.get("CapaciteNom"))
    if value is None or value <= 0:
        return None
    return value


def _sensitive_zone(attributes):
    """(en zone sensible, nom de la zone) - (None, None) si non renseigne."""
    code = str(attributes.get("CdEuZS") or "").strip()
    name = str(attributes.get("NomZS") or "").strip()
    if not code:
        return None, None
    if code.upper().startswith(HORS_ZONE_SENSIBLE):
        return False, None
    return True, name or None


def norms(capacity_eh, in_sensitive_zone):
    """Seuils de rejet applicables a une station, selon l'arrete de 2015.

    capacity_eh a None laisse tous les seuils vides : sans capacite, la
    station n'est rattachable a aucune classe, et rien ne serait plus
    trompeur que de lui prêter les seuils de la plus petite.

    L'azote et le phosphore ne sont exiges qu'en zone sensible et au-dela de
    10 000 EH. Une station qui n'y est pas soumise garde ces champs vides -
    et non a zero, qui se lirait comme une norme d'une severite absolue.
    """
    empty = {
        "norme_dbo5_mg_l": None, "norme_dbo5_rdt_pct": None,
        "norme_dco_mg_l": None, "norme_dco_rdt_pct": None,
        "norme_mes_mg_l": None, "norme_mes_rdt_pct": None,
        "norme_ngl_mg_l": None, "norme_ngl_rdt_pct": None,
        "norme_pt_mg_l": None, "norme_pt_rdt_pct": None,
        "norme_classe": None,
    }
    if capacity_eh is None:
        return empty

    classe = "grande" if capacity_eh >= SEUIL_ERU_EH else "petite"
    values = dict(empty)
    values["norme_classe"] = (
        "≥ 2 000 EH" if classe == "grande" else "< 2 000 EH"
    )
    values["norme_dbo5_mg_l"], values["norme_dbo5_rdt_pct"] = NORMES_DBO5[classe]
    values["norme_dco_mg_l"], values["norme_dco_rdt_pct"] = NORMES_DCO[classe]
    values["norme_mes_mg_l"], values["norme_mes_rdt_pct"] = NORMES_MES[classe]

    if in_sensitive_zone and capacity_eh > SEUIL_NUTRIMENTS_EH:
        niveau = ("haute" if capacity_eh > SEUIL_NUTRIMENTS_HAUT_EH
                  else "moyenne")
        values["norme_ngl_mg_l"], values["norme_ngl_rdt_pct"] = NORMES_NGL[niveau]
        values["norme_pt_mg_l"], values["norme_pt_rdt_pct"] = NORMES_PT[niveau]
    return values


def _load_rate(capacity_eh, incoming_eh):
    """Taux de charge en %, ou None. Au-dela de 100 %, la station est saturee."""
    if not capacity_eh or incoming_eh is None or incoming_eh <= 0:
        return None
    return 100.0 * incoming_eh / capacity_eh


def _in_service(attributes):
    """Une date de mise hors service, meme passee, retire la station du parc."""
    return not str(attributes.get("DateMiseHorServiceOuvrageDepollution")
                   or "").strip()


def stations(basin, progress=None):
    """Stations de traitement des eaux usees implantees dans le bassin.

    Le service ne filtre que sur l'emprise : l'appartenance au bassin reel
    est verifiee par sandre.features_in, qui teste l'intersection avec le
    polygone. Une station voisine du bassin mais hors de lui n'a rien a faire
    dans le releve - elle ne rejette pas dedans.
    """
    if progress:
        progress("Stations de traitement des eaux usées (Sandre)...")

    records = []
    for feature, geometry in sandre.features_in(LAYER_STEU, basin):
        attributes = sandre.attributes(feature)
        point = geometry.asPoint()
        capacity = _capacity(attributes)
        sensitive, zone_name = _sensitive_zone(attributes)
        incoming = sandre.as_float(attributes.get("SomChrgMaxEntree"))
        if incoming is not None and incoming <= 0:
            incoming = None

        record = {
            "code": attributes.get("CdOuvrageDepollution"),
            "nom": (attributes.get("NomOuvrageDepollution") or "").strip()
                   or None,
            "capacite_eh": capacity,
            "charge_max_eh": incoming,
            "taux_charge_pct": _load_rate(capacity, incoming),
            "nature": attributes.get("LbNatureSystTraitementEauxUsees"),
            "type_ouvrage": attributes.get("LbTypeOuvrageDepollution"),
            "en_service": _in_service(attributes),
            "date_service": attributes.get(
                "DateMiseServiceOuvrageDepollution"),
            "date_hors_service": attributes.get(
                "DateMiseHorServiceOuvrageDepollution"),
            "autosurveillance": attributes.get("LbExistAutosurv"),
            "conformite_autosurv": attributes.get(
                "LbConformiteAutosurveillance"),
            "zone_sensible": sensitive,
            "nom_zone_sensible": zone_name,
            "agglomeration": attributes.get("NomAgglomerationAssainissement"),
            "commune": attributes.get("LbCommuneLocalisation"),
            "systeme_collecte": attributes.get("LbSystemeCollecte"),
            "maj": attributes.get("DateMAJSTEU"),
            "norme_source": NORME_SOURCE,
            "x": point.x(),
            "y": point.y(),
        }
        record.update(norms(capacity, sensitive))
        records.append(record)

    # La plus grosse station d'abord : c'est elle qui pese sur le milieu, et
    # c'est par elle qu'on lit un rapport.
    records.sort(key=lambda r: -(r["capacite_eh"] or 0.0))

    en_service = [r for r in records if r["en_service"]]
    capacites = [r["capacite_eh"] for r in en_service if r["capacite_eh"]]
    charges = [r["charge_max_eh"] for r in en_service if r["charge_max_eh"]]
    return {
        "nb": len(records),
        "nb_en_service": len(en_service),
        "nb_capacite_connue": len(capacites),
        "capacite_totale_eh": sum(capacites) if capacites else None,
        "capacite_max_eh": max(capacites) if capacites else None,
        "charge_totale_eh": sum(charges) if charges else None,
        "nb_zone_sensible": sum(1 for r in en_service if r["zone_sensible"]),
        "nb_avec_autosurv": sum(
            1 for r in en_service
            if str(r["autosurveillance"] or "").lower().startswith("prés")
        ),
        "nb_sup_2000_eh": sum(
            1 for r in en_service
            if (r["capacite_eh"] or 0) >= SEUIL_ERU_EH
        ),
        "stations": records[:MAX_DETAIL],
        "source": "Stations de traitement des eaux usées (Sandre) — normes "
                  "calculées d'après l'arrêté du 21 juillet 2015",
    }


def compute(basin, with_steu=True, progress=None):
    """Releve des STEU du bassin.

    Une couche indisponible laisse la partie a None sans faire echouer le
    reste, comme pour les obstacles : le Sandre rend son service inegalement
    selon les heures.
    """
    values = {"steu": None, "erreurs": []}
    if not with_steu:
        return values
    try:
        values["steu"] = stations(basin, progress=progress)
    except Exception as exc:      # noqa: BLE001 - toute panne du service
        values["erreurs"].append("Stations de traitement : {0}".format(exc))
    return values
