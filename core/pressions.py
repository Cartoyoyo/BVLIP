# -*- coding: utf-8 -*-
"""Pression anthropique du bassin : sols pollues et rejets industriels.

Quatre inventaires nationaux, tous servis par Georisques (BRGM / ministere
de la Transition ecologique), qui disent ce que l'activite humaine a laisse
ou laisse encore dans le bassin, a cote de ce que les STEU rejettent et de
ce que les prelevements retirent :

  BASIAS   anciens sites industriels et activites de service. Un inventaire
           historique : il dit qu'une activite potentiellement polluante a
           existe, pas qu'il y a pollution.
  BASOL    sites et sols pollues, ou potentiellement pollues, appelant une
           action des pouvoirs publics. La pollution y est averee ou
           fortement suspectee.
  SIS      secteurs d'information sur les sols : les terrains ou l'Etat a
           connaissance d'une pollution justifiant des etudes de sol en cas
           de changement d'usage. Des surfaces, et non des points.
  IREP     etablissements tenus de declarer leurs rejets et leurs dechets
           au registre des emissions polluantes. C'est la seule des quatre
           qui parle du present.

Le service est un WFS 2.0 qui sert le Lambert 93, filtre sur l'emprise et
pagine comme la Geoplateforme ; seul le nom du format GeoJSON change. Il
passe donc par geoservices, qui en connait les reessais. L'appartenance au
bassin, elle, se teste ici sur le contour reel : l'emprise rectangulaire d'un
bassin fait couramment le double de sa surface.
"""

from .clip import PreparedBasin, geometry_of
from .geoservices import GeoserviceError, wfs_pages

URL = "https://www.georisques.gouv.fr/services"
OUTPUT_FORMAT = "geojson"

LAYER_BASIAS = "SSP_ETS_GE_POINT"
LAYER_BASOL = "SSP_INSTR_GE_POINT"
LAYER_SIS = "SSP_CLASSIF_SIS_GE"
LAYER_IREP = "ETABLISSEMENTS_POLLUEURS"

# Pages plus petites que celles de la Geoplateforme : le service est plus
# lent a repondre, et une page de mille points arrive bien avant le delai.
PAGE_SIZE = 1000
TIMEOUT = 90

# Plafond du releve detaille, comme pour les STEU : un bassin industriel
# porte plusieurs centaines d'anciens sites BASIAS, et chacun devient une
# ligne dans le rapport.
MAX_DETAIL = 500

# (cle, couche, libelle de l'inventaire). La cle sert aussi de valeur au
# champ "inventaire" de la couche QGIS, qui la colore.
INVENTAIRES = (
    ("basias", LAYER_BASIAS, "Ancien site industriel (BASIAS)"),
    ("basol", LAYER_BASOL, "Site pollué (BASOL)"),
    ("sis", LAYER_SIS, "Secteur d'information sur les sols (SIS)"),
    ("irep", LAYER_IREP, "Établissement déclarant ses rejets (IREP)"),
)
LABELS = {key: label for key, _layer, label in INVENTAIRES}

SOURCE = ("Géorisques (BRGM / ministère de la Transition écologique) — "
          "BASIAS, BASOL, SIS et registre IREP")


def _text(properties, *keys):
    """Premier attribut renseigne parmi ceux proposes, ou None."""
    for key in keys:
        value = properties.get(key)
        if value not in (None, ""):
            text = str(value).strip()
            if text:
                return text
    return None


def _record(key, properties, clipped):
    """Une entite, reduite a ce que le rapport et la couche en montrent."""
    if key == "basias":
        record = {
            "code": _text(properties, "code_inventaire", "code_metier"),
            "nom": _text(properties, "nom_etablissement"),
            "etat": _text(properties, "etat_activite"),
            "fiche": _text(properties, "fiche_risque"),
        }
    elif key == "basol":
        record = {
            "code": _text(properties, "id_inventaire_instruction",
                          "code_metier"),
            "nom": _text(properties, "nom_etablissement"),
            "etat": _text(properties, "statut_instruction"),
            "fiche": None,
        }
    elif key == "sis":
        record = {
            "code": _text(properties, "id_inventaire_classification",
                          "code_metier"),
            "nom": _text(properties, "nom_etablissement"),
            "etat": None,
            "fiche": None,
        }
    else:
        record = {
            "code": _text(properties, "identifiant", "idetab"),
            "nom": _text(properties, "nom"),
            # Le registre ne donne que le code APE : il dit le secteur
            # d'activite, ce qui est deja l'essentiel pour un bassin.
            "etat": _text(properties, "codeape"),
            "fiche": None,
        }
    record["inventaire"] = key
    record["commune"] = _text(properties, "nom_commune", "cp")
    record["geometrie"] = clipped
    if key == "sis":
        record["surface_ha"] = clipped.area() / 1e4
        point = clipped.pointOnSurface().asPoint()
    else:
        record["surface_ha"] = None
        point = clipped.asPoint() if not clipped.isMultipart() else \
            clipped.pointOnSurface().asPoint()
    record["x"] = point.x()
    record["y"] = point.y()
    return record


def inventory(key, typename, basin, prepared):
    """Entites d'un inventaire comprises dans le bassin."""
    box = basin.boundingBox()
    bbox = (box.xMinimum(), box.yMinimum(), box.xMaximum(), box.yMaximum())
    records = []
    for page in wfs_pages(typename, bbox=bbox, page_size=PAGE_SIZE,
                          max_features=None, timeout=TIMEOUT, url_base=URL,
                          output_format=OUTPUT_FORMAT):
        for feature in page:
            clipped = prepared.clip(geometry_of(feature))
            if clipped is None:
                continue
            records.append(_record(key, feature.get("properties") or {},
                                   clipped))
        del page
    records.sort(key=lambda r: (str(r["commune"] or ""), str(r["nom"] or "")))
    return records


def compute(basin, keys=None, progress=None):
    """Releve des quatre inventaires, ou de ceux demandes.

    Un inventaire indisponible laisse sa partie a None sans emporter les
    autres, comme pour les obstacles : Georisques rend son service
    inegalement selon les heures.
    """
    wanted = None if keys is None else set(keys)
    values = {"erreurs": [], "source": SOURCE}
    prepared = PreparedBasin(basin)
    for key, typename, label in INVENTAIRES:
        if wanted is not None and key not in wanted:
            values[key] = None
            continue
        if progress:
            progress("{0} (Géorisques)...".format(label))
        try:
            records = inventory(key, typename, basin, prepared)
        except GeoserviceError as exc:
            values[key] = None
            values["erreurs"].append("{0} : {1}".format(label, exc))
            continue
        values[key] = {
            "nb": len(records),
            "surface_ha": (sum(r["surface_ha"] or 0.0 for r in records)
                           if key == "sis" else None),
            "sites": records[:MAX_DETAIL],
        }
    return values
