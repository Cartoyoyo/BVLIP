# -*- coding: utf-8 -*-
"""Zonages environnementaux recoupant le bassin versant.

Dix couches nationales, de deux natures qu'il ne faut pas confondre :

  inventaire     ZNIEFF de type I et II. Elles ne protegent rien - ce sont
                 des inventaires scientifiques - mais elles signalent ce
                 qu'un amenagement devra justifier d'ignorer.
  protection     Natura 2000 (ZSC au titre des habitats, ZPS au titre des
                 oiseaux), arretes de protection de biotope, reserves
                 naturelles nationales et regionales, sites Ramsar. Celles-la
                 opposent un regime juridique.

Les surfaces ne s'additionnent pas. Une ZNIEFF de type I est presque toujours
incluse dans une ZNIEFF de type II, une ZSC et une ZPS se superposent sur les
memes vallees : sommer les dix lignes annoncerait couramment plus de 100 %
d'un bassin. Le total est donc une union geometrique, calculee comme telle, et
c'est la seule valeur du tableau qui puisse se comparer a la surface du bassin.

Toutes servies par la Geoplateforme, en GeoJSON pagine - voir geoservices. Le
catalogue portait a l'origine deux zonages de pression, servis par le Sandre
en WFS 1.1 : la zone vulnerable aux nitrates et la zone sensible a
l'eutrophisation. Les deux ont ete retirees, non pour ce qu'elles disaient
mais pour la fiabilite du service qui les servait - repondant tantot en une
seconde, tantot en plusieurs dizaines, sans rapport avec la requete ni le
filtre d'emprise applique. La lenteur de l'eutrophisation avait d'abord ete
absorbee en la parallelisant avec le reste plutot qu'en la retirant ; la
meme instabilite s'est ensuite revelee sur les nitrates, ce qui a tranche la
question pour les deux : mieux vaut un catalogue plus court et fiable qu'un
zonage de plus dont on ne sait jamais s'il coutera une seconde ou une minute.

Les dix couches restantes sont interrogees en parallele - voir compute() -
plutot qu'une a une : chacune attend son propre aller-retour reseau, sans
dependre des autres.
"""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from qgis.core import QgsGeometry, QgsJsonUtils

from .geoservices import GeoserviceError, wfs_pages

# (cle, couche, libelle, nature, couleur)
#
# L'ordre est celui du rapport : les inventaires d'abord parce qu'ils sont les
# plus etendus, les protections ensuite, les pressions en dernier.
#
# La couleur sert a la couche QGIS et a la carte du rapport, une teinte par
# zonage. Elle suit la nature plutot que le hasard : verts pour les
# inventaires ZNIEFF, bleus et violets pour les protections reglementaires,
# turquoises pour les territoires geres. Un lecteur qui ne connait pas les
# sigles voit deja de quel ordre releve chaque polygone.
#
# Les teintes sont volontairement franches et saturees, choisies pour se
# detacher nettement du fond de plan et rester reperables meme en couche
# translucide ou sur un ecran de terrain en plein soleil.
ZONAGES = (
    ("znieff1", "patrinat_znieff1:znieff1",
     "ZNIEFF de type I", "inventaire", "#39FF14"),
    ("znieff2", "patrinat_znieff2:znieff2",
     "ZNIEFF de type II", "inventaire", "#ADFF2F"),
    ("zsc", "patrinat_sic:sic",
     "Natura 2000 — ZSC, directive Habitats", "protection", "#0066FF"),
    ("zps", "patrinat_zps:zps",
     "Natura 2000 — ZPS, directive Oiseaux", "protection", "#00BFFF"),
    ("apb", "patrinat_apb:apb",
     "Arrêté de protection de biotope", "protection", "#9D00FF"),
    ("rnn", "patrinat_rnn:rnn",
     "Réserve naturelle nationale", "protection", "#7A00CC"),
    ("rnr", "patrinat_rnr:rnr",
     "Réserve naturelle régionale", "protection", "#E000FF"),
    ("pnr", "patrinat_pnr:pnr",
     "Parc naturel régional", "protection", "#00FFB2"),
    ("ramsar", "patrinat_ramsar:ramsar",
     "Site Ramsar", "protection", "#00FFFF"),
    ("zhumide", "TOURBIERES_ZONES-HUMIDES.BCAE:bcae",
     "Zones humides et tourbières BCAE", "protection", "#FF00A6"),
)

# Attributs portant le nom du site, dans l'ordre de preference. Les couches de
# l'INPN partagent un schema unique (nom_site, id_mnhn, url_fiche) ; la couche
# BCAE a le sien.
NAME_KEYS = ("nom_site", "type_zone")
CODE_KEYS = ("id_mnhn", "id_local")
URL_KEYS = ("url_fiche",)

# Les geometries retenues sont unies par paquets plutot qu'en une fois. Une
# union de plusieurs milliers de polygones - la couche BCAE en compte beaucoup
# sur un bassin tourbeux - se paie en memoire autant qu'en temps, la ou une
# union progressive ne garde qu'un seul resultat en cours.
UNION_BATCH = 200


class ProtectedAreasError(RuntimeError):
    """Les zonages n'ont pas pu etre etablis."""


def _first(properties, keys):
    for key in keys:
        value = properties.get(key)
        if value not in (None, ""):
            return str(value)
    return None


def _union(geometries):
    """Union d'une liste de geometries, par paquets."""
    merged = None
    for start in range(0, len(geometries), UNION_BATCH):
        batch = list(geometries[start:start + UNION_BATCH])
        if merged is not None:
            batch.append(merged)
        merged = QgsGeometry.unaryUnion(batch)
    return merged


def _clip(geometry, basin):
    if geometry is None or geometry.isEmpty():
        return None
    clipped = geometry.intersection(basin)
    if clipped.isEmpty() or clipped.area() <= 0:
        return None
    return clipped


def _sites(typename, basin, bbox):
    """Sites d'une couche de la Geoplateforme rencontrant le bassin."""
    for page in wfs_pages(typename, bbox=bbox, timeout=90):
        for feature in page:
            geometry = QgsGeometry(
                QgsJsonUtils.geometryFromGeoJson(
                    json.dumps(feature["geometry"])
                )
            )
            clipped = _clip(geometry, basin)
            if clipped is not None:
                yield feature.get("properties") or {}, clipped
        del page


def _zonage(entry, basin, total, bbox):
    """Une couche : ses sites, sa surface d'union, sa part du bassin."""
    key, typename, label, nature, color = entry

    sites = []
    geometries = []
    for properties, clipped in _sites(typename, basin, bbox):
        area = clipped.area()
        sites.append({
            "nom": _first(properties, NAME_KEYS) or label,
            "code": _first(properties, CODE_KEYS),
            "url": _first(properties, URL_KEYS),
            "surface_ha": area / 1e4,
            "part_pct": 100.0 * area / total if total else None,
            # La part decoupee sur le bassin, et non le site entier : c'est
            # elle qu'on cartographie, sans quoi un parc naturel regional
            # deborderait de plusieurs departements autour du bassin.
            "geometrie": clipped,
        })
        geometries.append(clipped)

    if not geometries:
        # Aucun site : la case reste vide plutot que de porter un zero, qui se
        # confondrait avec une couche interrogee sans succes. Le total, lui,
        # vaut bien zero et dit que le calcul a eu lieu.
        return {
            "cle": key, "libelle": label, "nature": nature, "couleur": color,
            "surface_ha": None, "part_pct": None, "nb_sites": 0,
            "sites": [], "geometrie": None,
        }

    merged = _union(geometries)
    area = merged.area() if merged is not None else 0.0
    sites.sort(key=lambda site: -site["surface_ha"])
    return {
        "cle": key, "libelle": label, "nature": nature, "couleur": color,
        "surface_ha": area / 1e4,
        "part_pct": 100.0 * area / total if total else None,
        "nb_sites": len(sites),
        "sites": sites,
        "geometrie": merged,
    }


def _zonage_safe(entry, basin, total, bbox):
    """Une couche, sans lever : (resultat, erreur), l'un des deux valant None.

    Necessaire pour ramasser le resultat d'un futur sans que l'exception
    d'une couche n'echappe au fil qui l'a lancee.
    """
    try:
        return _zonage(entry, basin, total, bbox), None
    except (GeoserviceError, RuntimeError) as exc:
        return None, "{0} : {1}".format(entry[2], exc)


def compute(basin, keys=None, progress=None):
    """Zonages environnementaux du bassin, une requete par couche, de front.

    keys restreint le relevé aux zonages demandes, dans l'ordre de la table ;
    None les prend tous. Chaque couche attend son propre aller-retour
    reseau, et rien ne les rend dependantes l'une de l'autre : dix requetes
    sequentielles font facilement plusieurs secondes, lancees ensemble le
    total se rapproche de la plus lente d'entre elles.

    Une couche indisponible ne fait pas echouer les suivantes : elle est
    signalee dans la liste des erreurs et le rapport reste produit.
    """
    total = basin.area()
    if total <= 0:
        raise ProtectedAreasError("Bassin de surface nulle.")

    box = basin.boundingBox()
    bbox = (box.xMinimum(), box.yMinimum(), box.xMaximum(), box.yMaximum())
    wanted = None if keys is None else set(keys)
    entries = [e for e in ZONAGES if wanted is None or e[0] in wanted]

    results = {}
    erreurs = []

    if len(entries) == 1:
        result, error = _zonage_safe(entries[0], basin, total, bbox)
        if error:
            erreurs.append(error)
        else:
            results[entries[0][0]] = result
        if progress:
            progress("Zonages : {0}...".format(entries[0][2]))
    elif entries:
        if progress:
            progress("Zonages : {0} couches, en parallèle...".format(
                len(entries)))
        with ThreadPoolExecutor(max_workers=len(entries)) as pool:
            futures = {
                pool.submit(_zonage_safe, entry, basin, total, bbox): entry
                for entry in entries
            }
            for future in as_completed(futures):
                entry = futures[future]
                result, error = future.result()
                if progress:
                    progress("Zonages : {0}...".format(entry[2]))
                if error:
                    erreurs.append(error)
                else:
                    results[entry[0]] = result

    # L'ordre du catalogue est reconstitue apres coup : les reponses du pool
    # arrivent dans l'ordre ou le serveur les rend, pas dans celui de la
    # table, et le rapport doit toujours lire les zonages dans le meme ordre.
    zonages = [results[e[0]] for e in entries if e[0] in results]

    # Le total est une union et non une somme : voir l'en-tete du module.
    covered = _union([z["geometrie"] for z in zonages if z["geometrie"]])
    union_area = covered.area() if covered is not None else 0.0

    # Seule l'union par zonage est jetee : elle n'a servi qu'au total. Les
    # geometries des sites, elles, alimentent la couche QGIS des zonages.
    for zonage in zonages:
        del zonage["geometrie"]

    return {
        "zonages": zonages,
        "total_ha": union_area / 1e4,
        # L'union est deja decoupee sur le bassin : elle ne peut pas le
        # deborder, et le plafond ne corrige qu'une derive d'arrondi qui
        # ferait afficher 100,00000000000226 % dans une exportation brute.
        "total_pct": min(100.0, 100.0 * union_area / total),
        "nb_sites": sum(z["nb_sites"] for z in zonages),
        "erreurs": erreurs,
        "source": "INPN / Patrinat (Géoplateforme)",
    }
