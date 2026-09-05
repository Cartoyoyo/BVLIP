# -*- coding: utf-8 -*-
"""Zonages environnementaux recoupant le bassin versant.

Douze couches nationales, de trois natures qu'il ne faut pas confondre :

  inventaire     ZNIEFF de type I et II. Elles ne protegent rien - ce sont
                 des inventaires scientifiques - mais elles signalent ce
                 qu'un amenagement devra justifier d'ignorer.
  protection     Natura 2000 (ZSC au titre des habitats, ZPS au titre des
                 oiseaux), arretes de protection de biotope, reserves
                 naturelles nationales et regionales, sites Ramsar. Celles-la
                 opposent un regime juridique.
  pression       zones vulnerables aux nitrates et zones sensibles a
                 l'eutrophisation. Elles ne disent pas ce qu'il y a de
                 remarquable dans le bassin, mais ce qu'on lui fait subir.

Les surfaces ne s'additionnent pas. Une ZNIEFF de type I est presque toujours
incluse dans une ZNIEFF de type II, une ZSC et une ZPS se superposent sur les
memes vallees : sommer les douze lignes annoncerait couramment plus de 100 %
d'un bassin. Le total est donc une union geometrique, calculee comme telle, et
c'est la seule valeur du tableau qui puisse se comparer a la surface du bassin.

Les sources sont deux services distincts : la Geoplateforme sert les zonages
de l'INPN sous forme de GeoJSON pagine, le Sandre les deux zonages de la
directive nitrates et de la directive eaux residuaires urbaines en WFS 1.1.
Le detail est dans geoservices et dans sandre ; ici on ne voit qu'une couche
a lire et une surface a cumuler.
"""

import json

from qgis.core import QgsGeometry, QgsJsonUtils

from . import sandre
from .geoservices import GeoserviceError, wfs_pages

# (cle, source, couche, libelle, nature, couleur)
#
# L'ordre est celui du rapport : les inventaires d'abord parce qu'ils sont les
# plus etendus, les protections ensuite, les pressions en dernier.
#
# La couleur sert a la couche QGIS et a la carte du rapport, une teinte par
# zonage. Elle suit la nature plutot que le hasard : verts pour les
# inventaires ZNIEFF, bleus et violets pour les protections reglementaires,
# turquoises pour les territoires geres, ocre et terre pour les pressions
# subies. Un lecteur qui ne connait pas les sigles voit deja de quel ordre
# releve chaque polygone.
#
# Les teintes sont volontairement rabattues, loin des couleurs franches d'une
# palette d'ecran. Sur la carte du rapport, une vingtaine de polygones
# translucides se superposent au-dessus d'un fond de plan deja charge : des
# couleurs saturees y font une bouillie ou plus rien ne se distingue, alors
# que des tons rompus laissent voir et le fond, et le chevelu, et les
# recouvrements.
ZONAGES = (
    ("znieff1", "geopf", "patrinat_znieff1:znieff1",
     "ZNIEFF de type I", "inventaire", "#4f9d69"),
    ("znieff2", "geopf", "patrinat_znieff2:znieff2",
     "ZNIEFF de type II", "inventaire", "#a3c4a8"),
    ("zsc", "geopf", "patrinat_sic:sic",
     "Natura 2000 — ZSC, directive Habitats", "protection", "#4a7fa5"),
    ("zps", "geopf", "patrinat_zps:zps",
     "Natura 2000 — ZPS, directive Oiseaux", "protection", "#93b4cc"),
    ("apb", "geopf", "patrinat_apb:apb",
     "Arrêté de protection de biotope", "protection", "#8a6ea8"),
    ("rnn", "geopf", "patrinat_rnn:rnn",
     "Réserve naturelle nationale", "protection", "#6b4f80"),
    ("rnr", "geopf", "patrinat_rnr:rnr",
     "Réserve naturelle régionale", "protection", "#ac96c4"),
    ("pnr", "geopf", "patrinat_pnr:pnr",
     "Parc naturel régional", "protection", "#4f9d94"),
    ("ramsar", "geopf", "patrinat_ramsar:ramsar",
     "Site Ramsar", "protection", "#7fbfb5"),
    ("zhumide", "geopf", "TOURBIERES_ZONES-HUMIDES.BCAE:bcae",
     "Zones humides et tourbières BCAE", "protection", "#a9cfc9"),
    ("nitrate", "sandre", "sa:ZoneVuln_delimitation_FXX",
     "Zone vulnérable aux nitrates", "pression", "#c9954f"),
    ("eutroph", "sandre", "sa:ZoneSensible_FXX_ZRPE_2",
     "Zone sensible à l'eutrophisation", "pression", "#b5705f"),
)

# Attributs portant le nom du site, dans l'ordre de preference. Les couches de
# l'INPN partagent un schema unique (nom_site, id_mnhn, url_fiche) ; celles du
# Sandre et la couche BCAE ont chacune le leur.
NAME_KEYS = ("nom_site", "NomZoneVuln", "NomZS", "NomCourtZS", "type_zone")
CODE_KEYS = ("id_mnhn", "CdEuZoneVuln", "CdEuZS", "id_local")
URL_KEYS = ("url_fiche", "URLTexteReglem")

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


def _geopf_sites(typename, basin, bbox):
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


def _sandre_sites(typename, basin):
    """Sites d'une couche Sandre rencontrant le bassin."""
    for feature, geometry in sandre.features_in(typename, basin):
        clipped = _clip(geometry, basin)
        if clipped is not None:
            yield sandre.attributes(feature), clipped


def _zonage(entry, basin, total, bbox):
    """Une couche : ses sites, sa surface d'union, sa part du bassin."""
    key, source, typename, label, nature, color = entry
    reader = (_geopf_sites(typename, basin, bbox) if source == "geopf"
              else _sandre_sites(typename, basin))

    sites = []
    geometries = []
    for properties, clipped in reader:
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


def compute(basin, keys=None, progress=None):
    """Zonages environnementaux du bassin, couche par couche.

    keys restreint le relevé aux zonages demandes, dans l'ordre de la table ;
    None les prend tous. Interroger douze couches nationales prend une bonne
    vingtaine de secondes sur un bassin moyen, et l'utilisateur qui n'a
    besoin que de Natura 2000 n'a pas a payer les onze autres.

    Une couche indisponible ne fait pas echouer les suivantes : elle est
    signalee dans la liste des erreurs et le rapport reste produit.
    """
    total = basin.area()
    if total <= 0:
        raise ProtectedAreasError("Bassin de surface nulle.")

    box = basin.boundingBox()
    bbox = (box.xMinimum(), box.yMinimum(), box.xMaximum(), box.yMaximum())
    wanted = None if keys is None else set(keys)

    zonages = []
    erreurs = []
    for entry in ZONAGES:
        if wanted is not None and entry[0] not in wanted:
            continue
        if progress:
            progress("Zonages : {0}...".format(entry[3]))
        try:
            zonages.append(_zonage(entry, basin, total, bbox))
        except (GeoserviceError, RuntimeError) as exc:
            erreurs.append("{0} : {1}".format(entry[3], exc))

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
        "source": "INPN / Patrinat (Géoplateforme) et Sandre (eaufrance)",
    }
