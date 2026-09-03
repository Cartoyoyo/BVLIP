# -*- coding: utf-8 -*-
"""Mise en forme du resultat : champs, couches memoire, habillage.

Trois couches decrivent un bassin :
    bassin_versant   le polygone, porteur de toutes les caracteristiques
    exutoire         le point retenu, et d'ou il vient
    cours_d_eau_amont  les troncons BD TOPO draines par l'exutoire, chacun
                       porteur de sa longueur en metres

Les couches sont creees en memoire. Rien n'est ecrit sur disque : l'utilisateur
exporte ce qu'il veut garder par le menu habituel de QGIS, et un essai qui ne
convient pas se ferme sans laisser de fichier derriere lui.

La table du bassin est decrite une seule fois, dans BASIN_FIELDS. Chaque entree
porte le nom technique du champ, son type, sa precision, l'endroit ou lire sa
valeur, et son intitule complet avec son unite. Cet intitule devient l'alias de
la couche : c'est lui que voit l'utilisateur dans la table attributaire et dans
le rapport, si bien qu'aucune valeur n'est lisible sans son unite.
"""

from datetime import datetime

from qgis.core import (
    QgsCoordinateReferenceSystem, QgsFeature, QgsField, QgsFields, QgsGeometry,
    QgsPointXY, QgsVectorLayer,
)
CRS = QgsCoordinateReferenceSystem("EPSG:2154")

# Depuis QGIS 3.38, le constructeur de QgsField prenant un QVariant.Type est
# deprecie au profit de QMetaType.Type. On prend le moderne quand il existe et
# on retombe sur l'ancien sinon, pour rester compatible avec les versions ou
# QMetaType.Type n'est pas expose par PyQt.
try:
    from qgis.PyQt.QtCore import QMetaType

    D = QMetaType.Type.Double
    S = QMetaType.Type.QString
    B = QMetaType.Type.Bool
    INT = QMetaType.Type.Int
    _MODERN_FIELDS = True
except (ImportError, AttributeError):  # pragma: no cover - QGIS anciens
    from qgis.PyQt.QtCore import QVariant

    D = QVariant.Type.Double
    S = QVariant.Type.String
    B = QVariant.Type.Bool
    INT = QVariant.Type.Int
    _MODERN_FIELDS = False

# (nom, type, longueur, precision, cle de lecture, intitule avec unite)
BASIN_FIELDS = [
    ("id_bv", S, 40, 0, "identite.id_bv",
     "Identifiant du bassin"),
    ("date_calcul", S, 20, 0, "identite.date_calcul",
     "Date du calcul"),

    # --- Geometrie et forme
    ("surface_km2", D, 14, 4, "metriques.surface_km2",
     "Surface (km²)"),
    ("surface_ha", D, 14, 2, "metriques.surface_ha",
     "Surface (ha)"),
    ("perimetre_km", D, 12, 3, "metriques.perimetre_km",
     "Périmètre (km)"),
    ("perim_brut_km", D, 12, 3, "identite.perimetre_brut_km",
     "Périmètre avant simplification (km)"),
    ("simplif_m", D, 6, 1, "identite.tolerance_simplif_m",
     "Tolérance de simplification du contour (m)"),
    ("gravelius", D, 8, 3, "metriques.gravelius",
     "Indice de compacité de Gravelius (sans unité)"),
    ("rect_long_m", D, 12, 1, "metriques.rect_longueur_m",
     "Rectangle équivalent — longueur (m)"),
    ("rect_larg_m", D, 12, 1, "metriques.rect_largeur_m",
     "Rectangle équivalent — largeur (m)"),

    # --- Altimetrie
    ("z_min_m", D, 10, 1, "metriques.z_min_m",
     "Altitude minimale (m NGF)"),
    ("z_max_m", D, 10, 1, "metriques.z_max_m",
     "Altitude maximale (m NGF)"),
    ("z_moyen_m", D, 10, 1, "metriques.z_moyen_m",
     "Altitude moyenne (m NGF)"),
    ("z_median_m", D, 10, 1, "metriques.z_median_m",
     "Altitude médiane (m NGF)"),
    ("z_hypso_5_m", D, 10, 1, "metriques.z_hypso_5_m",
     "Altitude dépassée par 5 % de la surface (m NGF)"),
    ("z_hypso_95_m", D, 10, 1, "metriques.z_hypso_95_m",
     "Altitude dépassée par 95 % de la surface (m NGF)"),
    ("denivelee_m", D, 10, 1, "metriques.denivelee_m",
     "Dénivelée totale, maxi moins mini (m)"),
    ("deniv_utile_m", D, 10, 1, "metriques.denivelee_utile_m",
     "Dénivelée utile, H5 % moins H95 % (m)"),

    # --- Pentes
    ("pente_deg", D, 8, 2, "metriques.pente_moyenne_deg",
     "Pente moyenne du terrain (degrés)"),
    ("pente_pct", D, 8, 2, "metriques.pente_moyenne_pct",
     "Pente moyenne du terrain (%)"),
    ("pente_med", D, 8, 2, "metriques.pente_mediane_deg",
     "Pente médiane du terrain (degrés)"),
    ("ig_m_par_km", D, 10, 2, "metriques.indice_pente_global_mkm",
     "Indice de pente global Ig (m/km)"),
    ("deniv_spec_m", D, 10, 1, "metriques.denivelee_specifique_m",
     "Dénivelée spécifique Ds (m)"),

    # --- Hydrographie
    ("long_chem_km", D, 10, 3, "metriques.long_cheminement_km",
     "Plus long cheminement hydraulique (km)"),
    ("lin_hydro_km", D, 10, 3, "metriques.lineaire_hydro_km",
     "Linéaire hydrographique BD TOPO dans le bassin (km)"),
    ("dens_drainage", D, 8, 3, "metriques.densite_drainage_kmkm2",
     "Densité de drainage (km/km²)"),
    ("reseau_dedans", D, 6, 1, "identite.part_reseau_pct",
     "Réseau amont contenu dans le bassin (% du linéaire)"),

    # --- Temps de concentration
    ("tc_kirpich_h", D, 8, 2, "tc.kirpich_h",
     "Temps de concentration — Kirpich (heures)"),
    ("tc_giandotti_h", D, 8, 2, "tc.giandotti_h",
     "Temps de concentration — Giandotti (heures)"),
    ("tc_passini_h", D, 8, 2, "tc.passini_h",
     "Temps de concentration — Passini (heures)"),
    ("tc_ventura_h", D, 8, 2, "tc.ventura_h",
     "Temps de concentration — Ventura (heures)"),
    ("tc_moyen_h", D, 8, 2, "tc.moyen_h",
     "Temps de concentration — moyenne des quatre (heures)"),

    # --- Occupation du sol
    ("ocs_dominante", S, 60, 0, "ocs.classe_dominante",
     "Occupation du sol dominante (Corine Land Cover 2018)"),
    ("ocs_dom_pct", D, 6, 1, "ocs.classe_dominante_pct",
     "Part de la classe dominante (% de la surface)"),
    ("ocs_artif_pct", D, 6, 1, "ocs.artificialise_pct",
     "Territoires artificialisés (% de la surface)"),
    ("ocs_agri_pct", D, 6, 1, "ocs.agricole_pct",
     "Territoires agricoles (% de la surface)"),
    ("ocs_foret_pct", D, 6, 1, "ocs.foret_pct",
     "Forêts et milieux semi-naturels (% de la surface)"),
    ("ocs_humide_pct", D, 6, 1, "ocs.humide_pct",
     "Zones humides (% de la surface)"),
    ("ocs_eau_pct", D, 6, 1, "ocs.eau_pct",
     "Surfaces en eau (% de la surface)"),
    ("bati_ha", D, 10, 3, "ocs.batiment_ha",
     "Emprise au sol des bâtiments BD TOPO (ha)"),
    ("bati_pct", D, 6, 2, "ocs.batiment_pct",
     "Emprise au sol des bâtiments (% de la surface)"),
    ("bati_nb", INT, 8, 0, "ocs.batiment_nb",
     "Nombre de bâtiments BD TOPO"),
    ("zone_hab_pct", D, 6, 2, "ocs.zone_habitation_pct",
     "Zones d'habitation BD TOPO (% de la surface)"),

    # --- Masse d'eau DCE
    ("me_code_eu", S, 20, 0, "masse_eau.code_eu",
     "Masse d'eau DCE — code européen"),
    ("me_nom", S, 200, 0, "masse_eau.nom_bv",
     "Masse d'eau DCE — dénomination"),
    ("me_surface_km2", D, 12, 2, "masse_eau.surface_bv_km2",
     "Masse d'eau DCE — surface de son bassin versant (km²)"),
    ("me_categorie", S, 20, 0, "masse_eau.categorie",
     "Masse d'eau DCE — catégorie Sandre"),
    ("me_exut_dedans", B, 1, 0, "masse_eau.exutoire_dans_le_bv",
     "Exutoire situé dans le bassin de la masse d'eau"),

    # --- Provenance de l'exutoire
    ("x_exutoire", D, 12, 2, "identite.x_exutoire",
     "Exutoire retenu — X (m, Lambert 93)"),
    ("y_exutoire", D, 12, 2, "identite.y_exutoire",
     "Exutoire retenu — Y (m, Lambert 93)"),
    ("x_clic", D, 12, 2, "identite.x_clic",
     "Point cliqué — X (m, Lambert 93)"),
    ("y_clic", D, 12, 2, "identite.y_clic",
     "Point cliqué — Y (m, Lambert 93)"),
    ("dist_reseau_m", D, 10, 1, "identite.dist_reseau_m",
     "Distance du point cliqué au réseau BD TOPO (m)"),
    ("recalage_mnt_m", D, 10, 1, "identite.recalage_mnt_m",
     "Recalage de l'exutoire sur le talweg du MNT (m)"),

    # --- Contexte et sources
    ("zone_hydro", S, 120, 0, "identite.zone_hydro",
     "Zone hydrographique BD TOPO"),
    ("code_zone", S, 20, 0, "identite.code_zone",
     "Zone hydrographique — code BD Carthage"),
    ("cours_d_eau", S, 120, 0, "identite.cours_d_eau",
     "Cours d'eau de l'exutoire"),
    ("code_hydro", S, 30, 0, "identite.code_hydro",
     "Tronçon d'exutoire — code hydrographique"),
    ("mnt_resolution", D, 6, 1, "identite.mnt_resolution",
     "Résolution du modèle numérique de terrain (m)"),
    ("mnt_elargi", B, 1, 0, "identite.mnt_elargi",
     "Maille élargie faute de mémoire"),
    ("mnt_affine", B, 1, 0, "identite.mnt_affine",
     "Recalculé à la maille la plus fine (bassin recadré)"),
    ("mnt_source", S, 80, 0, "identite.mnt_source",
     "Source du modèle numérique de terrain"),
]

OUTLET_FIELDS = [
    ("id_bv", S, 40, 0, None, "Identifiant du bassin"),
    ("origine", S, 30, 0, None, "Étape de détermination du point"),
    ("x", D, 12, 2, None, "X (m, Lambert 93)"),
    ("y", D, 12, 2, None, "Y (m, Lambert 93)"),
]

# Attributs BD TOPO repris sur chaque troncon. Le toponyme n'est renseigne
# que sur un peu plus de la moitie du reseau - 266 troncons sur 473 pour un
# bassin d'essai, 32 noms distincts - mais c'est justement ce qui permet de
# lire une carte : on y reconnait la Besbre, le Sapey, le Coindre.
#
# La persistance est renseignee partout et vaut son poids en hydrologie :
# sur le meme bassin, 302 troncons intermittents pour 171 permanents.
STREAM_FIELDS = [
    ("id_bv", S, 40, 0, None, "Identifiant du bassin"),
    ("nom", S, 120, 0, "cpx_toponyme_de_cours_d_eau",
     "Nom du cours d'eau"),
    ("code_hydro", S, 30, 0, "code_hydrographique",
     "Code hydrographique du tronçon"),
    ("nature", S, 40, 0, "nature",
     "Nature de l'écoulement"),
    ("persistance", S, 20, 0, "persistance",
     "Persistance de l'écoulement"),
    ("largeur", S, 30, 0, "classe_de_largeur",
     "Classe de largeur"),
    ("longueur_m", D, 12, 1, None, "Longueur du tronçon (m)"),
    ("cleabs", S, 40, 0, None, "Identifiant BD TOPO du tronçon"),
]

# Regroupement pour le rapport : titre de section, puis champs dans l'ordre.
REPORT_SECTIONS = [
    ("Forme et dimensions", [
        "surface_km2", "surface_ha", "perimetre_km", "gravelius",
        "rect_long_m", "rect_larg_m",
    ]),
    ("Relief", [
        "z_min_m", "z_max_m", "z_moyen_m", "denivelee_m", "deniv_utile_m",
        "pente_pct", "ig_m_par_km", "deniv_spec_m",
    ]),
    ("Hydrographie", [
        "long_chem_km", "lin_hydro_km", "dens_drainage", "reseau_dedans",
        "tc_kirpich_h", "tc_giandotti_h", "tc_passini_h", "tc_ventura_h",
    ]),
    ("Occupation du sol", [
        "ocs_dominante", "ocs_artif_pct", "ocs_agri_pct", "ocs_foret_pct",
        "bati_ha", "bati_nb", "zone_hab_pct",
    ]),
    ("Masse d'eau DCE", [
        "me_code_eu", "me_nom", "me_surface_km2", "me_categorie",
    ]),
    ("Exutoire et sources", [
        "x_exutoire", "y_exutoire", "dist_reseau_m", "recalage_mnt_m",
        "zone_hydro", "code_zone", "mnt_resolution", "mnt_elargi",
        "mnt_affine", "mnt_source",
    ]),
]

ALIASES = {name: label for name, _t, _l, _p, _k, label in BASIN_FIELDS}


def _fields(definition):
    fields = QgsFields()
    for entry in definition:
        name, kind, length, precision = entry[:4]
        if _MODERN_FIELDS:
            fields.append(QgsField(name, kind, "", length, precision))
        else:  # pragma: no cover - QGIS anciens
            fields.append(QgsField(name, kind, len=length, prec=precision))
    return fields


def _apply_aliases(layer, definition):
    """Pose les intitules complets en alias.

    La table attributaire et le rapport affichent alors des libelles portant
    leur unite plutot que des noms de colonnes abreges : aucune valeur ne peut
    etre lue sans savoir en quoi elle est exprimee.
    """
    index = {field.name(): i for i, field in enumerate(layer.fields())}
    for entry in definition:
        name, label = entry[0], entry[5]
        if name in index and label:
            layer.setFieldAlias(index[name], label)


def _memory_layer(kind, name, definition):
    layer = QgsVectorLayer(
        "{0}?crs={1}".format(kind, CRS.authid()), name, "memory"
    )
    layer.dataProvider().addAttributes(_fields(definition).toList())
    layer.updateFields()
    _apply_aliases(layer, definition)
    return layer


# ------------------------------------------------------------- Attributs

CLC_LEVEL1_FIELDS = {
    "1": "artificialise_pct",
    "2": "agricole_pct",
    "3": "foret_pct",
    "4": "humide_pct",
    "5": "eau_pct",
}


def flatten_land_cover(land_cover):
    """Reduit le detail de l'occupation du sol aux champs de la table."""
    if not land_cover:
        return {}
    values = {}
    corine = land_cover.get("corine")
    if corine:
        # Une classe absente du bassin vaut 0 %, pas "inconnu" : CLC couvre le
        # territoire sans trou, l'absence est donc une mesure.
        for field in CLC_LEVEL1_FIELDS.values():
            values[field] = 0.0
        for group in corine.get("niveaux1", []):
            field = CLC_LEVEL1_FIELDS.get(group["code"])
            if field:
                values[field] = group["part_pct"]
        classes = corine.get("classes") or []
        if classes:
            values["classe_dominante"] = classes[0]["libelle"]
            values["classe_dominante_pct"] = classes[0]["part_pct"]
    built = land_cover.get("bati")
    if built:
        for key in ("batiment_ha", "batiment_pct", "batiment_nb",
                    "zone_habitation_pct"):
            values[key] = built.get(key)
    return values


# Maille la plus fine que le service sache servir en natif ; au-dela, le
# resultat est un reechantillonnage.
FINEST_RESOLUTION = 5.0


def build_attributes(delineation_result, network_result, click_point,
                     metrics_values=None, water_body=None, basin_id=None,
                     land_cover=None, refined=None):
    """Assemble les valeurs des champs du bassin, par groupe de provenance."""
    basin_id = basin_id or datetime.now().strftime("BV_%Y%m%d_%H%M%S")
    stream = network_result.get("stream") or {}
    zone = network_result.get("zone") or {}
    metrics_values = metrics_values or {}

    area = delineation_result["area"]
    identity = {
        "id_bv": basin_id,
        "date_calcul": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "x_exutoire": delineation_result["outlet"][0],
        "y_exutoire": delineation_result["outlet"][1],
        "x_clic": click_point[0],
        "y_clic": click_point[1],
        "dist_reseau_m": network_result.get("snap_distance"),
        "recalage_mnt_m": delineation_result["snap_shift"],
        "zone_hydro": zone.get("toponyme"),
        "code_zone": zone.get("code_bdcarthage"),
        "cours_d_eau": stream.get("cpx_toponyme_de_cours_d_eau"),
        "code_hydro": stream.get("code_hydrographique"),
        "mnt_resolution": delineation_result["dem"]["resolution"],
        "mnt_source": "RGE ALTI (IGN) via Géoplateforme",
        # Une maille elargie ne change pas la surface, mais elle adoucit les
        # versants et raccourcit le contour : perimetre, Gravelius, pente et
        # cheminement portent alors quelques pour cent d'incertitude en plus.
        # Le lecteur du rapport doit pouvoir le savoir.
        "mnt_elargi": (
            delineation_result["dem"]["resolution"] > FINEST_RESOLUTION
        ),
        "mnt_affine": bool(refined),
        # Perimetre avant simplification : garde la trace de l'escalier de
        # mailles, qui allonge le contour d'environ 30 % et gonflerait
        # l'indice de Gravelius d'autant s'il etait conserve tel quel.
        "perimetre_brut_km": (
            delineation_result.get("perimetre_brut_m", 0.0) / 1000.0 or None
        ),
        "tolerance_simplif_m": delineation_result.get("tolerance_simplif_m"),
        # Un bassin contient les cours d'eau qu'il draine : cette part doit
        # etre proche de 100 %. Elle est conservee pour que le lecteur du
        # rapport puisse en juger lui-meme.
        "part_reseau_pct": (
            None if delineation_result.get("part_reseau_dedans") is None
            else 100.0 * delineation_result["part_reseau_dedans"]
        ),
    }

    # Sans calcul de metriques, surface et perimetre restent renseignes :
    # ce sont des proprietes du polygone, pas des caracteristiques derivees.
    base_metrics = {
        "surface_km2": area / 1e6,
        "surface_ha": area / 1e4,
        "perimetre_km": delineation_result["perimeter"] / 1000.0,
    }
    base_metrics.update(
        {k: v for k, v in metrics_values.items()
         if not isinstance(v, (list, tuple, dict))}
    )

    return {
        "identite": identity,
        "metriques": base_metrics,
        "tc": metrics_values.get("temps_concentration") or {},
        "masse_eau": water_body or {},
        "ocs": flatten_land_cover(land_cover),
    }, basin_id


def basin_feature(fields, geometry, groups):
    feature = QgsFeature(fields)
    feature.setGeometry(geometry)
    for name, _kind, _length, _precision, key, _label in BASIN_FIELDS:
        group, _, attribute = key.partition(".")
        feature[name] = groups.get(group, {}).get(attribute)
    return feature


def outlet_features(fields, result, click_point, basin_id):
    """Les points successifs par lesquels l'exutoire a ete determine.

    Les conserver tous n'est pas de la coquetterie : quand une surface
    surprend, l'ecart entre le clic, l'accrochage et le recalage est la
    premiere chose a regarder.
    """
    points = [
        ("point cliqué", click_point),
        ("accroché sur BD TOPO", result["network"]["outlet"]),
        ("recalé sur le talweg", result["delineation"]["outlet"]),
    ]
    values = result.get("metrics") or {}
    if values.get("point_le_plus_eloigne"):
        points.append(
            ("point le plus éloigné", values["point_le_plus_eloigne"])
        )
    for origin, (x, y) in points:
        feature = QgsFeature(fields)
        feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x, y)))
        feature["id_bv"] = basin_id
        feature["origine"] = origin
        feature["x"] = x
        feature["y"] = y
        yield feature


def stream_features(fields, upstream, basin_id):
    """Un troncon par entite, avec ses attributs BD TOPO utiles.

    La cle de lecture, cinquieme element de STREAM_FIELDS, designe l'attribut
    d'origine : les champs sans cle sont calcules ou viennent du contexte.
    """
    mapping = [(name, key) for name, _t, _l, _p, key, _lbl in STREAM_FIELDS
               if key]
    for record in upstream:
        properties = record["properties"]
        feature = QgsFeature(fields)
        feature.setGeometry(record["geometry"])
        feature["id_bv"] = basin_id
        feature["cleabs"] = record["id"]
        feature["longueur_m"] = record["geometry"].length()
        for name, key in mapping:
            value = properties.get(key)
            feature[name] = None if value in ("", []) else value
        yield feature


# --------------------------------------------------------- Couches memoire

def build_layers(result, click_point, basin_id=None):
    """Cree les trois couches memoire decrivant le bassin.

    Renvoie (couches, identifiant, valeurs par groupe). Les couches ne sont pas
    ajoutees au projet : c'est a l'appelant de decider ou les ranger.
    """
    groups, basin_id = build_attributes(
        result["delineation"], result["network"], click_point,
        result["metrics"], result["water_body"], basin_id,
        result["land_cover"], result.get("affinage"),
    )

    basin = _memory_layer("Polygon", "Bassin versant", BASIN_FIELDS)
    basin.dataProvider().addFeature(
        basin_feature(basin.fields(), result["delineation"]["geometry"], groups)
    )
    basin.updateExtents()

    outlets = _memory_layer("Point", "Exutoire", OUTLET_FIELDS)
    outlets.dataProvider().addFeatures(list(
        outlet_features(outlets.fields(), result, click_point, basin_id)
    ))
    outlets.updateExtents()

    layers = {"bassin": basin, "exutoire": outlets, "reseau": None}

    upstream = result["network"].get("upstream") or []
    if upstream:
        streams = _memory_layer("MultiLineString", "Cours d'eau amont",
                                STREAM_FIELDS)
        streams.dataProvider().addFeatures(list(
            stream_features(streams.fields(), upstream, basin_id)
        ))
        streams.updateExtents()
        layers["reseau"] = streams

    return layers, basin_id, groups


# --------------------------------------------------------------- Affichage

def style_layers(layers):
    """Applique une symbologie lisible aux trois couches."""
    from qgis.core import (
        QgsCategorizedSymbolRenderer, QgsMarkerSymbol, QgsRendererCategory,
    )
    from qgis.PyQt.QtGui import QColor

    basin = layers["bassin"]
    symbol = basin.renderer().symbol()
    symbol.setColor(QColor(52, 152, 219, 55))
    symbol.symbolLayer(0).setStrokeColor(QColor(192, 57, 43))
    symbol.symbolLayer(0).setStrokeWidth(0.9)

    if layers.get("reseau") is not None:
        _style_streams(layers["reseau"])

    # Les quatre etats de l'exutoire se distinguent au premier coup d'oeil :
    # c'est ce qui permet de voir d'un regard de combien le point a bouge.
    styles = {
        "point cliqué": ("#7f8c8d", "circle", 2.4),
        "accroché sur BD TOPO": ("#f39c12", "circle", 2.8),
        "recalé sur le talweg": ("#c0392b", "star", 4.5),
        "point le plus éloigné": ("#8e44ad", "triangle", 3.4),
    }
    categories = []
    for value, (color, shape, size) in styles.items():
        marker = QgsMarkerSymbol.createSimple({
            "name": shape, "color": color, "outline_color": "white",
            "outline_width": "0.3", "size": str(size),
        })
        categories.append(QgsRendererCategory(value, marker, value))
    layers["exutoire"].setRenderer(
        QgsCategorizedSymbolRenderer("origine", categories)
    )


def group_label(groups):
    """Nom du groupe de couches, tire de ce que le bassin a d'identifiable.

    Deux calculs successifs ne doivent pas se retrouver sous deux groupes
    homonymes : on ne saurait plus lequel est lequel dans le panneau des
    couches. Le nom du cours d'eau, a defaut la zone hydrographique, suivi de
    la surface, suffit a les distinguer d'un coup d'oeil.
    """
    identity = groups.get("identite", {})
    metrics_values = groups.get("metriques", {})
    label = identity.get("cours_d_eau") or identity.get("zone_hydro")
    if label:
        # Les libelles de la BD Carthage sont en capitales et truffes de
        # mentions « (NC) » qui n'apprennent rien au lecteur ; ceux de la
        # BD TOPO empilent parfois plusieurs denominations separees par une
        # barre oblique. On garde la premiere, sans les mentions, en casse
        # ordinaire.
        label = str(label).split("/")[0]
        label = label.replace("(NC)", "").replace("(nc)", "")
        label = " ".join(label.split())
        label = label[:1].upper() + label[1:].lower()
        if len(label) > 45:
            label = label[:44].rstrip() + "…"
    else:
        label = identity.get("id_bv", "")
    area = metrics_values.get("surface_km2")
    if area is not None:
        return "BVLIP - {0} ({1:.2f} km²)".format(label, area)
    return "BVLIP - {0}".format(label)


def _style_streams(layer):
    """Trait plein pour les ecoulements permanents, tirete pour les autres.

    La distinction est portee par la BD TOPO sur la totalite des troncons et
    change la lecture d'une carte : sur un bassin d'essai, deux tiers du
    lineaire sont intermittents. Les afficher tous du meme trait laisserait
    croire a un reseau en eau toute l'annee.
    """
    from qgis.core import (
        QgsCategorizedSymbolRenderer, QgsLineSymbol, QgsRendererCategory,
    )
    from qgis.PyQt.QtCore import Qt

    categories = []
    for valeur, libelle, style in (
        ("Permanent", "Permanent", Qt.PenStyle.SolidLine),
        ("Intermittent", "Intermittent", Qt.PenStyle.DashLine),
    ):
        symbol = QgsLineSymbol.createSimple({
            "color": "41,128,185", "width": "0.45",
        })
        symbol.symbolLayer(0).setPenStyle(style)
        categories.append(QgsRendererCategory(valeur, symbol, libelle))

    # Tout ce qui n'est ni l'un ni l'autre - retenues, conduits - garde un
    # trait plein plus clair plutot que de disparaitre de la carte.
    autre = QgsLineSymbol.createSimple({"color": "127,179,213", "width": "0.4"})
    categories.append(QgsRendererCategory("", autre, "Autre"))

    layer.setRenderer(QgsCategorizedSymbolRenderer("persistance", categories))
    _label_streams(layer)


def _label_streams(layer):
    """Etiquette les troncons par leur toponyme, la ou il existe.

    Un peu plus de la moitie des troncons en portent un ; les autres restent
    muets, ce qui evite d'encombrer la carte de vides.
    """
    from qgis.core import (
        QgsPalLayerSettings, QgsTextBufferSettings, QgsTextFormat,
        QgsVectorLayerSimpleLabeling,
    )
    from qgis.PyQt.QtGui import QColor, QFont

    text_format = QgsTextFormat()
    font = QFont("Arial")
    font.setItalic(True)
    text_format.setFont(font)
    text_format.setSize(8)
    text_format.setColor(QColor(21, 67, 96))

    buffer_settings = QgsTextBufferSettings()
    buffer_settings.setEnabled(True)
    buffer_settings.setSize(0.8)
    buffer_settings.setColor(QColor(255, 255, 255))
    text_format.setBuffer(buffer_settings)

    settings = QgsPalLayerSettings()
    settings.fieldName = "nom"
    settings.setFormat(text_format)
    # Le libelle suit la courbe du cours d'eau, comme sur une carte
    # topographique ; une etiquette horizontale posee sur un meandre serait
    # illisible.
    placement = getattr(QgsPalLayerSettings, "Placement", None)
    if placement is not None:
        settings.placement = placement.Curved
    layer.setLabeling(QgsVectorLayerSimpleLabeling(settings))
    layer.setLabelsEnabled(True)


def add_to_project(layers, group_name="BVLIP", iface=None, zoom=True):
    """Range les couches dans un groupe du projet et cadre la carte dessus."""
    from qgis.core import QgsProject

    style_layers(layers)
    project = QgsProject.instance()
    group = project.layerTreeRoot().insertGroup(0, group_name)

    for layer in (layers["exutoire"], layers.get("reseau"), layers["bassin"]):
        if layer is None:
            continue
        project.addMapLayer(layer, False)
        group.addLayer(layer)

    if zoom and iface is not None:
        extent = layers["bassin"].extent()
        extent.grow(extent.width() * 0.1)
        iface.mapCanvas().setExtent(extent)
        iface.mapCanvas().refresh()
    return group
