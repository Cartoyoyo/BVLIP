# -*- coding: utf-8 -*-
"""Mise en forme du resultat : champs, couches memoire, habillage.

Huit couches decrivent un bassin :
    bassin_versant   le polygone, porteur de toutes les caracteristiques
    exutoire         le point retenu, et d'ou il vient
    cours_d_eau_amont  les troncons BD TOPO draines par l'exutoire, chacun
                       porteur de sa longueur en metres
    zonages          les zonages environnementaux qui le recoupent, un
                     polygone par site, decoupe sur le bassin et colore
                     selon son type. Elle n'existe que s'il y a des zonages.
    parcelles        les parcelles declarees a la PAC, une par parcelle
                     anonyme du RPG, coloree par intitule de culture. Elle
                     n'existe que si le RPG a ete interroge.
    foret            les formations vegetales de la BD Foret v2, colorees
                     dans la gamme des verts. Elle n'existe que si la BD
                     Foret a ete interrogee.
    bio              les parcelles engagees en agriculture biologique,
                     hachurees sans fond pour se poser sur les parcelles PAC
                     sans leur prendre leur couleur.
    obstacles        les ouvrages du ROE, un point par obstacle : la couleur
                     dit la franchissabilite, la taille la hauteur de chute.

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

    # --- Obstacles a l'ecoulement et hydrometrie
    ("roe_nb", INT, 8, 0, "roe.nb",
     "Obstacles à l'écoulement ROE — nombre"),
    ("roe_exist_nb", INT, 8, 0, "roe.nb_existants",
     "Obstacles ROE encore existants — nombre"),
    ("roe_grenelle", INT, 8, 0, "roe.nb_grenelle",
     "Obstacles ROE classés Grenelle — nombre"),
    ("roe_passe_nb", INT, 8, 0, "roe.nb_avec_passe",
     "Obstacles ROE avec passe à poissons — nombre"),
    # La hauteur cumulee melange hauteurs mesurees et milieux de classe : voir
    # l'en-tete du module obstacles. L'intitule le dit, faute de quoi elle
    # serait lue comme une mesure.
    ("roe_h_cum_m", D, 10, 2, "roe.chute_cumulee_m",
     "ROE — chute cumulée, classes comprises (m)"),
    ("roe_h_max_m", D, 8, 2, "roe.chute_max_m",
     "Obstacles ROE — plus haute chute (m)"),
    ("roe_par_km", D, 8, 3, "roe.par_km",
     "Obstacles ROE par km de cours d'eau (nb/km)"),
    ("sitehydro_nb", INT, 8, 0, "hydrometrie.nb",
     "Sites hydrométriques Sandre — nombre"),
    ("hydro_codes", S, 200, 0, "hydrometrie.codes",
     "Sites hydrométriques — codes Sandre"),

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
    # Deux totaux distincts, et l'intitule doit dire lequel : le couvert de la
    # BD Foret comprend landes et formations herbacees, la surface boisee non.
    ("foret_ha", D, 12, 2, "foret.surface_ha",
     "Couvert BD Forêt v2, landes comprises (ha)"),
    ("foret_pct", D, 6, 2, "foret.part_pct",
     "Couvert BD Forêt v2, landes comprises (%)"),
    ("peupl_ha", D, 12, 2, "foret.boisee_ha",
     "Surface boisée, peuplements seuls (ha)"),
    ("peupl_pct", D, 6, 2, "foret.boisee_pct",
     "Surface boisée, peuplements seuls (% de la surface)"),
    ("foret_dom", S, 80, 0, "foret.dominante",
     "Formation forestière dominante (BD Forêt v2)"),
    ("foret_dom_pct", D, 6, 1, "foret.dominante_pct",
     "Part de la formation forestière dominante (%)"),
    ("foret_feui_pct", D, 6, 1, "foret.feuillus_pct",
     "Forêt de feuillus (% de la surface)"),
    ("foret_coni_pct", D, 6, 1, "foret.coniferes_pct",
     "Forêt de conifères (% de la surface)"),
    ("foret_mixt_pct", D, 6, 1, "foret.mixte_pct",
     "Forêt mixte (% de la surface)"),

    # --- Agriculture declaree (PAC)
    ("rpg_ha", D, 12, 2, "agri.surface_ha",
     "Surface déclarée à la PAC (ha)"),
    ("rpg_pct", D, 6, 2, "agri.part_pct",
     "Surface déclarée à la PAC (% de la surface)"),
    ("rpg_nb", INT, 8, 0, "agri.nb_parcelles",
     "Parcelles PAC dans le bassin — nombre"),
    ("rpg_moy_ha", D, 8, 2, "agri.taille_moyenne_ha",
     "Parcelle PAC — taille moyenne (ha)"),
    ("rpg_med_ha", D, 8, 2, "agri.taille_mediane_ha",
     "Parcelle PAC — taille médiane (ha)"),
    ("herbe_ha", D, 12, 2, "agri.herbe_ha",
     "Prairies et surfaces pastorales déclarées (ha)"),
    ("herbe_pct", D, 6, 2, "agri.herbe_pct",
     "Prairies et pastoral déclarés (% de la surface)"),
    ("rpg_cult_ha", D, 12, 2, "agri.cultures_ha",
     "Cultures déclarées, hors prairies (ha)"),
    ("rpg_cult_pct", D, 6, 2, "agri.cultures_pct",
     "Cultures déclarées, hors prairies (% de la surface)"),
    ("rpg_arable_pct", D, 6, 2, "agri.arable_pct",
     "Terres arables déclarées (% de la surface)"),
    ("rpg_perm_pct", D, 6, 2, "agri.permanente_pct",
     "Cultures permanentes déclarées (% de la surface)"),
    ("rpg_prairie_pct", D, 6, 2, "agri.prairie_pct",
     "Prairies permanentes déclarées (% de la surface)"),
    ("rpg_dominante", S, 120, 0, "agri.dominante",
     "Culture déclarée dominante (RPG)"),
    ("rpg_dom_pct", D, 6, 1, "agri.dominante_pct",
     "Part de la culture dominante (% de la surface)"),
    ("bio_ha", D, 12, 2, "agri.bio_certifie_ha",
     "Surface certifiée agriculture biologique (ha)"),
    ("bio_pct", D, 6, 2, "agri.bio_certifie_pct",
     "Certifiée agriculture biologique (% de la surface)"),
    ("conv_ha", D, 12, 2, "agri.bio_conversion_ha",
     "Surface en conversion biologique (ha)"),
    ("conv_pct", D, 6, 2, "agri.bio_conversion_pct",
     "En conversion biologique (% de la surface)"),
    ("bio_nb", INT, 8, 0, "agri.bio_nb",
     "Parcelles bio ou en conversion — nombre"),
    ("bio_declare", D, 6, 2, "agri.bio_part_declare",
     "Bio et conversion (% de la surface déclarée)"),
    ("bcae_ha", D, 12, 2, "agri.prairies_sensibles_ha",
     "Prairies sensibles BCAE (ha)"),
    ("bcae_pct", D, 6, 2, "agri.prairies_sensibles_pct",
     "Prairies sensibles BCAE (% de la surface)"),
    ("aoc_ha", D, 12, 2, "agri.aoc_ha",
     "Aires AOC viticoles (ha)"),
    ("aoc_pct", D, 6, 2, "agri.aoc_pct",
     "Aires AOC viticoles (% de la surface)"),

    # --- Zonages environnementaux
    ("znieff1_ha", D, 12, 2, "zonages.znieff1_ha",
     "ZNIEFF de type I (ha)"),
    ("znieff1_pct", D, 6, 1, "zonages.znieff1_pct",
     "ZNIEFF de type I (% de la surface)"),
    ("znieff2_ha", D, 12, 2, "zonages.znieff2_ha",
     "ZNIEFF de type II (ha)"),
    ("znieff2_pct", D, 6, 1, "zonages.znieff2_pct",
     "ZNIEFF de type II (% de la surface)"),
    ("zsc_ha", D, 12, 2, "zonages.zsc_ha",
     "Natura 2000 — ZSC, habitats (ha)"),
    ("zsc_pct", D, 6, 1, "zonages.zsc_pct",
     "Natura 2000 — ZSC, habitats (% de la surface)"),
    ("zps_ha", D, 12, 2, "zonages.zps_ha",
     "Natura 2000 — ZPS, oiseaux (ha)"),
    ("zps_pct", D, 6, 1, "zonages.zps_pct",
     "Natura 2000 — ZPS, oiseaux (% de la surface)"),
    ("apb_ha", D, 12, 2, "zonages.apb_ha",
     "Arrêté de protection de biotope (ha)"),
    ("apb_pct", D, 6, 1, "zonages.apb_pct",
     "Arrêté de protection de biotope (% de la surface)"),
    ("rnn_ha", D, 12, 2, "zonages.rnn_ha",
     "Réserve naturelle nationale (ha)"),
    ("rnn_pct", D, 6, 1, "zonages.rnn_pct",
     "Réserve naturelle nationale (% de la surface)"),
    ("rnr_ha", D, 12, 2, "zonages.rnr_ha",
     "Réserve naturelle régionale (ha)"),
    ("rnr_pct", D, 6, 1, "zonages.rnr_pct",
     "Réserve naturelle régionale (% de la surface)"),
    ("pnr_ha", D, 12, 2, "zonages.pnr_ha",
     "Parc naturel régional (ha)"),
    ("pnr_pct", D, 6, 1, "zonages.pnr_pct",
     "Parc naturel régional (% de la surface)"),
    ("ramsar_ha", D, 12, 2, "zonages.ramsar_ha",
     "Site Ramsar (ha)"),
    ("ramsar_pct", D, 6, 1, "zonages.ramsar_pct",
     "Site Ramsar (% de la surface)"),
    ("zhumide_ha", D, 12, 2, "zonages.zhumide_ha",
     "Zones humides et tourbières BCAE (ha)"),
    ("zhumide_pct", D, 6, 1, "zonages.zhumide_pct",
     "Zones humides et tourbières BCAE (% de la surface)"),
    ("nitrate_ha", D, 12, 2, "zonages.nitrate_ha",
     "Zone vulnérable aux nitrates (ha)"),
    ("nitrate_pct", D, 6, 1, "zonages.nitrate_pct",
     "Zone vulnérable aux nitrates (% de la surface)"),
    ("eutroph_ha", D, 12, 2, "zonages.eutroph_ha",
     "Zone sensible à l'eutrophisation (ha)"),
    ("eutroph_pct", D, 6, 1, "zonages.eutroph_pct",
     "Zone sensible à l'eutrophisation (% de la surface)"),
    ("zonage_ha", D, 12, 2, "zonages.total_ha",
     "Total sous zonage, sans double compte (ha)"),
    ("zonage_pct", D, 6, 1, "zonages.total_pct",
     "Total sous zonage, sans double compte (%)"),
    ("zonage_nb", INT, 8, 0, "zonages.nb_sites",
     "Nombre de sites de zonage recoupant le bassin"),

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
    ("meso_code_eu", S, 20, 0, "meso.code_eu",
     "Masse d'eau souterraine — code européen"),
    ("meso_nom", S, 200, 0, "meso.nom",
     "Masse d'eau souterraine — dénomination"),
    ("meso_ecoul", S, 60, 0, "meso.nature_ecoulement",
     "Masse d'eau souterraine — nature de l'écoulement"),
    ("meso_karst", B, 1, 0, "meso.karstique",
     "Masse d'eau souterraine karstique"),
    ("her1_code", S, 20, 0, "her.her1_code",
     "Hydroécorégion de niveau 1 — code"),
    ("her1_nom", S, 120, 0, "her.her1_nom",
     "Hydroécorégion de niveau 1"),
    ("her2_code", S, 20, 0, "her.her2_code",
     "Hydroécorégion de niveau 2 — code"),
    ("her2_nom", S, 120, 0, "her.her2_nom",
     "Hydroécorégion de niveau 2"),

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

# Aplat et contour des zonages.
#
# L'aplat est tres clair et le trait fin, parce que ces polygones se comptent
# par dizaines et se superposent. Le premier essai - aplat a 60 sur 255,
# contour a 0,5 mm - donnait une carte illisible : vingt-six contours francs
# qui se croisent l'emportaient sur le chevelu et sur le fond de plan. A 30 et
# 0,26 mm, les zonages se lisent sans prendre le pas sur ce qu'ils habillent,
# et le cumul des aplats continue de signaler les recouvrements.
ZONAGE_FILL_ALPHA = 30
ZONAGE_OUTLINE_MM = "0.26"

# Zonages environnementaux, un enregistrement par site et non par type : c'est
# le site qui porte un nom, un code et une fiche, et c'est de lui qu'on veut la
# forme sur la carte. Les geometries sont deja decoupees sur le bassin - voir
# protected - sans quoi un parc naturel regional deborderait de plusieurs
# departements autour de lui.
ZONAGE_FIELDS = [
    ("id_bv", S, 40, 0, None, "Identifiant du bassin"),
    ("zonage", S, 60, 0, None, "Type de zonage"),
    ("cle", S, 20, 0, None, "Code du type de zonage"),
    ("nature", S, 20, 0, None, "Nature : inventaire, protection, pression"),
    ("nom", S, 200, 0, None, "Nom du site"),
    ("code", S, 40, 0, None, "Code INPN ou Sandre du site"),
    ("surface_ha", D, 12, 2, None, "Surface dans le bassin (ha)"),
    ("part_pct", D, 6, 2, None, "Part du bassin (%)"),
    ("fiche", S, 254, 0, None, "Fiche descriptive en ligne"),
]

# Obstacles a l'ecoulement du ROE, un point par ouvrage recense dans le
# bassin. La hauteur de chute est portee telle que le module obstacles la
# rend, avec sa provenance : mesuree, ou reconstituee depuis la classe.
OBSTACLE_FIELDS = [
    ("id_bv", S, 40, 0, None, "Identifiant du bassin"),
    ("code", S, 20, 0, None, "Code ROE de l'ouvrage"),
    ("nom", S, 200, 0, None, "Nom de l'ouvrage"),
    ("type", S, 60, 0, None, "Type d'ouvrage (code Sandre)"),
    ("etat", S, 40, 0, None, "État de l'ouvrage"),
    ("chute_m", D, 8, 2, None, "Hauteur de chute (m)"),
    ("provenance", S, 20, 0, None, "Chute mesurée ou déduite de sa classe"),
    ("classe", S, 60, 0, None, "Classe de hauteur de chute"),
    ("passe", S, 20, 0, None, "Passe à poissons"),
    ("usage", S, 80, 0, None, "Usage principal de l'ouvrage"),
    ("grenelle", B, 1, 0, None, "Ouvrage classé Grenelle"),
    ("cours_eau", S, 120, 0, None, "Cours d'eau barré"),
]

# Formations vegetales de la BD Foret v2, une entite par polygone decoupe sur
# le bassin.
FOREST_FIELDS = [
    ("id_bv", S, 40, 0, None, "Identifiant du bassin"),
    ("formation", S, 120, 0, None, "Formation végétale (BD Forêt v2)"),
    ("essence", S, 60, 0, None, "Essence dominante"),
    ("surface_ha", D, 12, 4, None, "Surface dans le bassin (ha)"),
    ("part_pct", D, 6, 3, None, "Part du bassin (%)"),
]

# Parcelles engagees en agriculture biologique. Couche a part plutot qu'un
# champ de plus sur les parcelles PAC : elle se hachure au-dessus d'elles sans
# leur prendre leur couleur de culture, et se decoche seule dans le panneau.
BIO_FIELDS = [
    ("id_bv", S, 40, 0, None, "Identifiant du bassin"),
    ("statut", S, 30, 0, None, "Certifiée AB ou en conversion"),
    ("stade", S, 60, 0, None, "Stade de certification"),
    ("culture", S, 200, 0, None, "Culture déclarée"),
    ("surface_ha", D, 12, 4, None, "Surface dans le bassin (ha)"),
    ("part_pct", D, 6, 3, None, "Part du bassin (%)"),
]

# Parcelles declarees a la PAC, une entite par parcelle anonyme du RPG,
# decoupee sur le bassin. Le registre public ne porte aucun identifiant
# d'exploitation, et le plugin n'en lit aucun : ces entites disent ce qui est
# cultive, jamais par qui.
RPG_FIELDS = [
    ("id_bv", S, 40, 0, None, "Identifiant du bassin"),
    ("code", S, 10, 0, None, "Code culture du RPG"),
    ("culture", S, 200, 0, None, "Culture déclarée"),
    ("categorie", S, 40, 0, None, "Catégorie de culture du RPG"),
    ("nature", S, 20, 0, None, "Nature : herbe ou culture"),
    ("surface_ha", D, 12, 4, None, "Surface dans le bassin (ha)"),
    ("part_pct", D, 6, 3, None, "Part du bassin (%)"),
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
        "roe_nb", "roe_h_cum_m", "roe_par_km", "sitehydro_nb",
    ]),
    ("Occupation du sol", [
        "ocs_dominante", "ocs_artif_pct", "ocs_agri_pct", "ocs_foret_pct",
        "bati_ha", "bati_nb", "zone_hab_pct",
        "peupl_pct", "foret_feui_pct", "foret_coni_pct",
    ]),
    # Les zonages sont listes sans leur surface en hectares : la part du
    # bassin est ce qui se lit d'un coup d'oeil, et les hectares figurent
    # dans la table attributaire comme dans le classeur. Une ligne absente
    # signifie que le zonage ne recoupe pas le bassin - voir protected, ou
    # une couche sans site rend None et non zero.
    ("Agriculture déclarée (PAC)", [
        "rpg_pct", "rpg_nb", "rpg_med_ha", "herbe_pct", "rpg_cult_pct",
        "rpg_dominante", "bcae_pct", "aoc_pct",
    ]),
    ("Zonages environnementaux", [
        "znieff1_pct", "znieff2_pct", "zsc_pct", "zps_pct", "apb_pct",
        "rnn_pct", "rnr_pct", "pnr_pct", "ramsar_pct", "zhumide_pct",
        "nitrate_pct", "eutroph_pct", "zonage_pct", "zonage_nb",
    ]),
    ("Masses d'eau et hydroécorégion", [
        "me_code_eu", "me_nom", "me_surface_km2", "me_categorie",
        "meso_code_eu", "meso_nom", "meso_karst", "her1_nom", "her2_nom",
    ]),
    ("Exutoire et sources", [
        "x_exutoire", "y_exutoire", "dist_reseau_m", "recalage_mnt_m",
        "zone_hydro", "code_zone", "mnt_resolution", "mnt_elargi",
        "mnt_affine", "mnt_source",
    ]),
]

# Sections que les pages de detail reprennent en entier, avec leurs listes.
#
# Quand la page 1 n'a pas la place de les porter, elles ne sont pas reportees
# telles quelles : ce serait les ecrire deux fois, en resume puis en detail,
# a quelques centimetres d'ecart. Les titres doivent correspondre a ceux de
# REPORT_SECTIONS, ce que tools/check_fields verifie.
DETAILED_SECTIONS = (
    "Occupation du sol",
    "Agriculture déclarée (PAC)",
    "Zonages environnementaux",
    "Masses d'eau et hydroécorégion",
)

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


def flatten_forest(land_cover):
    """Champs du couvert forestier, tires de la BD Foret v2."""
    forest = (land_cover or {}).get("foret")
    if not forest:
        return {}
    return {
        key: forest.get(key)
        for key in ("surface_ha", "part_pct", "boisee_ha", "boisee_pct",
                    "dominante", "dominante_pct", "feuillus_pct",
                    "coniferes_pct", "mixte_pct")
    }


def flatten_agriculture(agriculture):
    """Champs de l'agriculture declaree, tires du RPG et de ses voisines."""
    agriculture = agriculture or {}
    rpg = agriculture.get("rpg") or {}
    values = {
        key: rpg.get(key)
        for key in ("surface_ha", "part_pct", "nb_parcelles",
                    "taille_moyenne_ha", "taille_mediane_ha",
                    "dominante", "dominante_pct",
                    "herbe_ha", "herbe_pct", "herbe_part_declare",
                    "cultures_ha", "cultures_pct", "cultures_part_declare")
    }
    # Les trois categories deviennent trois champs nommes : une part de
    # terres arables se lit dans une table attributaire, pas une liste.
    parts = {item["code"]: item["part_pct"]
             for item in rpg.get("categories") or ()}
    values["arable_pct"] = parts.get("TA")
    values["permanente_pct"] = parts.get("CP")
    values["prairie_pct"] = parts.get("PP")

    bio = agriculture.get("bio") or {}
    values["bio_certifie_ha"] = bio.get("certifie_ha")
    values["bio_certifie_pct"] = bio.get("certifie_pct")
    values["bio_conversion_ha"] = bio.get("conversion_ha")
    values["bio_conversion_pct"] = bio.get("conversion_pct")
    values["bio_nb"] = bio.get("nb_parcelles")
    values["bio_part_declare"] = bio.get("part_declare")

    prairies = agriculture.get("prairies") or {}
    values["prairies_sensibles_ha"] = prairies.get("surface_ha")
    values["prairies_sensibles_pct"] = prairies.get("part_pct")
    aoc = agriculture.get("aoc") or {}
    values["aoc_ha"] = aoc.get("surface_ha")
    values["aoc_pct"] = aoc.get("part_pct")
    return values


def flatten_protected(protected):
    """Une paire de champs par zonage, plus le total.

    Les cles sont celles de protected.ZONAGES : ajouter un zonage la-bas
    suffit a le voir apparaitre ici, a condition de lui ouvrir ses deux
    champs dans BASIN_FIELDS.
    """
    if not protected:
        return {}
    values = {
        "total_ha": protected.get("total_ha"),
        "total_pct": protected.get("total_pct"),
        "nb_sites": protected.get("nb_sites"),
    }
    for zonage in protected.get("zonages") or []:
        values[zonage["cle"] + "_ha"] = zonage["surface_ha"]
        values[zonage["cle"] + "_pct"] = zonage["part_pct"]
    return values


# Maille la plus fine que le service sache servir en natif ; au-dela, le
# resultat est un reechantillonnage.
FINEST_RESOLUTION = 5.0


def build_attributes(delineation_result, network_result, click_point,
                     metrics_values=None, water_body=None, basin_id=None,
                     land_cover=None, refined=None, protected=None,
                     structures=None, groundwater=None, hydroecoregion=None,
                     agriculture=None):
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

    structures = structures or {}
    return {
        "identite": identity,
        "metriques": base_metrics,
        "masse_eau": water_body or {},
        "meso": groundwater or {},
        "her": hydroecoregion or {},
        "ocs": flatten_land_cover(land_cover),
        "agri": flatten_agriculture(agriculture),
        "foret": flatten_forest(land_cover),
        "zonages": flatten_protected(protected),
        "roe": structures.get("roe") or {},
        "hydrometrie": structures.get("hydrometrie") or {},
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


def obstacle_features(fields, structures, basin_id):
    """Un point par obstacle a l'ecoulement recense dans le bassin."""
    from qgis.core import QgsPointXY

    sites = ((structures or {}).get("roe") or {}).get("sites") or []
    for site in sites:
        if site.get("x") is None or site.get("y") is None:
            continue
        feature = QgsFeature(fields)
        feature.setGeometry(
            QgsGeometry.fromPointXY(QgsPointXY(site["x"], site["y"])))
        feature["id_bv"] = basin_id
        feature["code"] = site["code"]
        feature["nom"] = site["nom"]
        feature["type"] = site["type"]
        feature["etat"] = site["etat"]
        feature["chute_m"] = site["chute_m"]
        feature["provenance"] = site["chute_origine"]
        feature["classe"] = site["chute_classe"]
        passe = site["passe_a_poissons"]
        feature["passe"] = ("non renseigné" if passe is None
                            else ("oui" if passe else "non"))
        feature["usage"] = site["usage"]
        feature["grenelle"] = site["grenelle"]
        feature["cours_eau"] = site["cours_d_eau"]
        yield feature


def forest_features(fields, land_cover, basin_id):
    """Un polygone par formation vegetale, de la plus vaste a la plus petite."""
    polygones = ((land_cover or {}).get("foret") or {}).get("polygones") or []
    polygones = [p for p in polygones
                 if p.get("geometrie") is not None
                 and not p["geometrie"].isEmpty()]
    polygones.sort(key=lambda p: -(p["surface_ha"] or 0.0))

    for item in polygones:
        feature = QgsFeature(fields)
        feature.setGeometry(QgsGeometry(item["geometrie"]))
        feature["id_bv"] = basin_id
        feature["formation"] = item["libelle"]
        feature["essence"] = item["essence"]
        feature["surface_ha"] = item["surface_ha"]
        feature["part_pct"] = item["part_pct"]
        yield feature


def bio_features(fields, agriculture, basin_id):
    """Un polygone par parcelle bio ou en conversion."""
    parcelles = ((agriculture or {}).get("bio") or {}).get("parcelles") or []
    parcelles = [p for p in parcelles
                 if p.get("geometrie") is not None
                 and not p["geometrie"].isEmpty()]
    parcelles.sort(key=lambda p: -(p["surface_ha"] or 0.0))
    for parcelle in parcelles:
        feature = QgsFeature(fields)
        feature.setGeometry(QgsGeometry(parcelle["geometrie"]))
        feature["id_bv"] = basin_id
        feature["statut"] = parcelle["statut"]
        feature["stade"] = parcelle["stade"]
        feature["culture"] = parcelle["culture"]
        feature["surface_ha"] = parcelle["surface_ha"]
        feature["part_pct"] = parcelle["part_pct"]
        yield feature


def rpg_features(fields, agriculture, basin_id):
    """Un polygone par parcelle declaree, de la plus vaste a la plus petite.

    Meme raison qu'aux zonages : QGIS dessine dans l'ordre d'arrivee et la
    derniere entite passe au-dessus. Une grande prairie posee en dernier
    couvrirait les parcelles de culture qu'elle entoure.
    """
    parcelles = ((agriculture or {}).get("rpg") or {}).get("parcelles") or []
    parcelles = [p for p in parcelles
                 if p.get("geometrie") is not None
                 and not p["geometrie"].isEmpty()]
    parcelles.sort(key=lambda p: -(p["surface_ha"] or 0.0))

    for parcelle in parcelles:
        feature = QgsFeature(fields)
        feature.setGeometry(QgsGeometry(parcelle["geometrie"]))
        feature["id_bv"] = basin_id
        feature["code"] = parcelle["code"]
        feature["culture"] = parcelle["libelle"]
        feature["categorie"] = parcelle["categorie"]
        feature["nature"] = "herbe" if parcelle["herbe"] else "culture"
        feature["surface_ha"] = parcelle["surface_ha"]
        feature["part_pct"] = parcelle["part_pct"]
        yield feature


def zonage_features(fields, protected, basin_id):
    """Un polygone par site de zonage, du plus vaste au plus petit.

    L'ordre n'est pas un detail d'ecriture : QGIS dessine les entites dans
    l'ordre ou elles arrivent, et la derniere passe au-dessus. Les sites sont
    donc classes par surface decroissante, pour que les petits se posent sur
    les grands. Range dans l'ordre du catalogue, la zone sensible a
    l'eutrophisation - cent pour cent du bassin sur la Besbre - arriverait en
    dernier et masquerait a elle seule les onze autres zonages.
    """
    sites = [
        (zonage, site)
        for zonage in (protected or {}).get("zonages") or []
        for site in zonage.get("sites") or []
        if site.get("geometrie") is not None
        and not site["geometrie"].isEmpty()
    ]
    sites.sort(key=lambda pair: -(pair[1]["surface_ha"] or 0.0))

    for zonage, site in sites:
        feature = QgsFeature(fields)
        feature.setGeometry(QgsGeometry(site["geometrie"]))
        feature["id_bv"] = basin_id
        feature["zonage"] = zonage["libelle"]
        feature["cle"] = zonage["cle"]
        feature["nature"] = zonage["nature"]
        feature["nom"] = site["nom"]
        feature["code"] = site["code"]
        feature["surface_ha"] = site["surface_ha"]
        feature["part_pct"] = site["part_pct"]
        feature["fiche"] = site["url"]
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
        result.get("protected"), result.get("structures"),
        result.get("groundwater"), result.get("hydroecoregion"),
        result.get("agriculture"),
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

    layers = {"bassin": basin, "exutoire": outlets, "reseau": None,
              "zonages": None, "parcelles": None, "foret": None,
              "bio": None, "obstacles": None}

    # Obstacles a l'ecoulement, si le ROE a ete interroge.
    roe_layer = _memory_layer("Point", "Obstacles à l'écoulement (ROE)",
                              OBSTACLE_FIELDS)
    ouvrages = list(obstacle_features(roe_layer.fields(),
                                      result.get("structures"), basin_id))
    if ouvrages:
        roe_layer.dataProvider().addFeatures(ouvrages)
        roe_layer.updateExtents()
        layers["obstacles"] = roe_layer

    # Parcelles engagees en bio, si la couche categorisee a ete interrogee.
    bio_layer = _memory_layer("MultiPolygon",
                              "Parcelles en agriculture biologique",
                              BIO_FIELDS)
    engagees = list(bio_features(bio_layer.fields(),
                                 result.get("agriculture"), basin_id))
    if engagees:
        bio_layer.dataProvider().addFeatures(engagees)
        bio_layer.updateExtents()
        layers["bio"] = bio_layer

    # Formations de la BD Foret, si elle a ete interrogee.
    foret_layer = _memory_layer("MultiPolygon", "Formations BD Forêt v2",
                                FOREST_FIELDS)
    formations = list(forest_features(foret_layer.fields(),
                                      result.get("land_cover"), basin_id))
    if formations:
        foret_layer.dataProvider().addFeatures(formations)
        foret_layer.updateExtents()
        layers["foret"] = foret_layer

    # Parcelles declarees a la PAC, si le RPG a ete interroge.
    rpg_layer = _memory_layer("MultiPolygon", "Parcelles PAC (RPG)",
                              RPG_FIELDS)
    parcelles = list(rpg_features(rpg_layer.fields(),
                                  result.get("agriculture"), basin_id))
    if parcelles:
        rpg_layer.dataProvider().addFeatures(parcelles)
        rpg_layer.updateExtents()
        layers["parcelles"] = rpg_layer

    # Les zonages n'ont de couche que s'il y en a : une couche vide dans le
    # panneau ferait croire a un calcul rate plutot qu'a un bassin sans
    # zonage.
    zonage_layer = _memory_layer("MultiPolygon", "Zonages environnementaux",
                                 ZONAGE_FIELDS)
    entites = list(zonage_features(zonage_layer.fields(),
                                   result.get("protected"), basin_id))
    if entites:
        zonage_layer.dataProvider().addFeatures(entites)
        zonage_layer.updateExtents()
        layers["zonages"] = zonage_layer

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
    """Applique une symbologie lisible aux couches produites."""
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

    if layers.get("zonages") is not None:
        _style_zonages(layers["zonages"])

    if layers.get("parcelles") is not None:
        _style_parcelles(layers["parcelles"])

    if layers.get("foret") is not None:
        _style_foret(layers["foret"])

    if layers.get("bio") is not None:
        _style_bio(layers["bio"])

    if layers.get("obstacles") is not None:
        _style_obstacles(layers["obstacles"])

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


def _style_zonages(layer):
    """Une teinte par type de zonage, en aplat translucide et contour franc.

    Les zonages se superposent par nature : sur un bassin de moyenne montagne,
    une ZNIEFF de type I, une ZNIEFF de type II, une ZSC et un parc naturel
    regional couvrent souvent le meme versant. Un aplat opaque n'en montrerait
    qu'un seul. D'ou la transparence, qui fait ressortir les recouvrements en
    fonces, et le contour plein, qui garde chaque limite lisible meme sous
    trois autres polygones.

    Les categories sont posees dans l'ordre du catalogue et non dans celui des
    entites : la legende suit ainsi le rapport, inventaires puis protections
    puis pressions, quel que soit l'ordre de dessin.
    """
    from qgis.core import (
        QgsCategorizedSymbolRenderer, QgsFillSymbol, QgsRendererCategory,
    )
    from qgis.PyQt.QtGui import QColor

    from .protected import ZONAGES

    presents = {feature["cle"] for feature in layer.getFeatures()}
    categories = []
    for key, _source, _typename, label, _nature, color in ZONAGES:
        if key not in presents:
            continue
        # La couleur passe en r,g,b,a et non en #rrggbbaa : QGIS ne lit pas
        # l'hexadecimal a huit chiffres et en tire une teinte sans rapport -
        # "#27ae60" suffixe de "40" rendait un aplat orange a la place du
        # vert, avec une transparence prise au hasard.
        tint = QColor(color)
        fill = "{0},{1},{2},{3}".format(
            tint.red(), tint.green(), tint.blue(), ZONAGE_FILL_ALPHA)
        symbol = QgsFillSymbol.createSimple({
            "color": fill,
            "outline_color": color,
            "outline_width": ZONAGE_OUTLINE_MM,
            "outline_style": "solid",
        })
        categories.append(QgsRendererCategory(key, symbol, label))
    if categories:
        layer.setRenderer(QgsCategorizedSymbolRenderer("cle", categories))
        layer.setOpacity(0.9)


# Longueur au-dela de laquelle un intitule est raccourci dans la legende.
# "Prairie permanente - herbe predominante (ressources fourrageres ligneuses
# absentes ou peu presentes)" fait cent caracteres : en legende de carte, il
# deborde de la page, et dans le panneau des couches il chasse tout le reste.
# La valeur de la categorie, elle, reste entiere - c'est elle qui sert au
# filtrage et a la table attributaire.
LEGEND_LABEL_MAX = 46

# Separateurs ou couper de preference : la coupure tombe alors sur une
# articulation du libelle plutot qu'au milieu d'un mot.
LEGEND_CUTS = (" (", " - ", ", ")


def short_label(text, limit=LEGEND_LABEL_MAX):
    """Intitule raccourci pour une legende, coupe a une articulation."""
    text = str(text or "")
    if len(text) <= limit:
        return text
    for cut in LEGEND_CUTS:
        position = text.find(cut)
        if 0 < position <= limit:
            return text[:position]
    return text[:limit - 1].rstrip() + "…"


def unique_short_labels(names, limit=LEGEND_LABEL_MAX):
    """Intitules raccourcis, mais deux fois le meme jamais.

    Couper a l'articulation rend "Surface pastorale" pour deux libelles qui
    ne disent pas la meme chose - l'un a herbe predominante, l'autre a
    ressources ligneuses. Une legende qui repete deux fois la meme ligne avec
    deux couleurs differentes ne se lit plus. Les libelles qui se
    telescoperaient sont donc coupes a la longueur, sans chercher
    d'articulation : c'est moins joli, mais cela reste distinct.
    """
    courts = {nom: short_label(nom, limit) for nom in names}
    compte = {}
    for court in courts.values():
        compte[court] = compte.get(court, 0) + 1
    for nom, court in list(courts.items()):
        if compte[court] > 1 and nom != court:
            courts[nom] = (nom[:limit - 1].rstrip() + "…"
                           if len(nom) > limit else nom)
    return courts


def _style_foret(layer):
    """Une teinte par formation vegetale, dans la gamme des verts.

    Les feuillus, les coniferes et les melanges se distinguent au premier
    coup d'oeil, et les landes comme les formations herbacees sortent de la
    gamme : ce ne sont pas des bois, et la carte ne doit pas les faire passer
    pour tels.
    """
    from qgis.core import (
        QgsCategorizedSymbolRenderer, QgsFillSymbol, QgsRendererCategory,
    )

    from .landcover import formation_color

    surfaces = {}
    for feature in layer.getFeatures():
        nom = feature["formation"]
        surfaces[nom] = surfaces.get(nom, 0.0) + (feature["surface_ha"] or 0.0)
    if not surfaces:
        return

    courts = unique_short_labels(surfaces)
    categories = []
    for nom in sorted(surfaces, key=lambda n: -surfaces[n]):
        symbol = QgsFillSymbol.createSimple({
            "color": formation_color(nom),
            "outline_color": "255,255,255,120",
            "outline_width": "0.12",
            "outline_style": "solid",
        })
        categories.append(
            QgsRendererCategory(nom, symbol, courts[nom]))
    layer.setRenderer(QgsCategorizedSymbolRenderer("formation", categories))
    layer.setOpacity(0.8)


# Symbologie des obstacles : la couleur dit la franchissabilite, la taille
# dit la hauteur de chute. Deux informations sur un meme point, qui sont
# justement les deux questions qu'on se pose devant un seuil.
OBSTACLE_STYLES = (
    ("oui", "#27ae60", "Passe à poissons"),
    ("non", "#c0392b", "Sans passe à poissons"),
    ("non renseigné", "#7f8c8d", "Franchissabilité non renseignée"),
)

# Bornes de la taille des points, en millimetres, entre une chute nulle et la
# plus haute rencontree. Une taille fixe ne dirait rien : sur la Besbre, un
# seuil de quarante centimetres et un barrage de quarante metres se
# ressembleraient trait pour trait.
OBSTACLE_SIZE_MIN = 1.8
OBSTACLE_SIZE_MAX = 6.0


def _style_obstacles(layer):
    """Points du ROE : couleur par franchissabilite, taille par chute.

    La taille est une propriete calculee et non une classification : la
    hauteur de chute est continue, et la decouper en paliers ferait croire a
    des categories qui n'existent pas. Les ouvrages sans hauteur connue
    gardent la taille minimale plutot que de disparaitre.
    """
    from qgis.core import (
        QgsCategorizedSymbolRenderer, QgsMarkerSymbol, QgsProperty,
        QgsRendererCategory, QgsSymbolLayer,
    )

    hauteurs = [f["chute_m"] for f in layer.getFeatures() if f["chute_m"]]
    maximum = max(hauteurs) if hauteurs else 1.0
    taille = (
        "coalesce(scale_linear(\"chute_m\", 0, {0}, {1}, {2}), {1})"
    ).format(max(maximum, 0.1), OBSTACLE_SIZE_MIN, OBSTACLE_SIZE_MAX)

    presents = {feature["passe"] for feature in layer.getFeatures()}
    categories = []
    for valeur, couleur, libelle in OBSTACLE_STYLES:
        if valeur not in presents:
            continue
        symbol = QgsMarkerSymbol.createSimple({
            "name": "circle", "color": couleur,
            "outline_color": "white", "outline_width": "0.3",
            "size": str(OBSTACLE_SIZE_MIN),
        })
        symbol.setDataDefinedSize(QgsProperty.fromExpression(taille))
        symbol.symbolLayer(0).setDataDefinedProperty(
            QgsSymbolLayer.Property.PropertySize,
            QgsProperty.fromExpression(taille))
        categories.append(QgsRendererCategory(valeur, symbol, libelle))
    if categories:
        layer.setRenderer(QgsCategorizedSymbolRenderer("passe", categories))


def _style_bio(layer):
    """Hachures sur les parcelles engagees en bio, sans fond.

    Une couche a part, posee au-dessus des parcelles PAC : les hachures
    marquent l'engagement sans effacer la couleur de la culture qui est
    dessous. C'est bien ce qu'on veut lire - quelle culture, et engagee ou
    non - et deux couches se decochent separement.

    Le certifie et la conversion se distinguent par l'inclinaison des traits :
    ce qui est acquis penche d'un cote, ce qui est en cours de l'autre.
    """
    from qgis.core import (
        QgsCategorizedSymbolRenderer, QgsFillSymbol,
        QgsLinePatternFillSymbolLayer, QgsRendererCategory,
    )
    from qgis.PyQt.QtGui import QColor

    styles = (
        ("Certifiée AB", 45.0, "#2f6d3a"),
        ("En conversion", 135.0, "#8a6a2f"),
    )
    presents = {feature["statut"] for feature in layer.getFeatures()}
    categories = []
    for statut, angle, couleur in styles:
        if statut not in presents:
            continue
        # Fond transparent, contour plein : la couleur de la culture reste
        # visible dessous.
        symbol = QgsFillSymbol.createSimple({
            "style": "no", "outline_color": couleur,
            "outline_width": "0.3", "outline_style": "solid",
        })
        # La hachure est un QgsLinePatternFillSymbolLayer, la seule classe qui
        # en produise. Un QgsFillSymbol.createSimple ne rend qu'un aplat, quel
        # que soit le nom qu'on lui passe.
        hachure = QgsLinePatternFillSymbolLayer()
        hachure.setLineAngle(angle)
        hachure.setDistance(1.6)
        hachure.setLineWidth(0.25)
        hachure.setColor(QColor(couleur))
        symbol.appendSymbolLayer(hachure)
        categories.append(QgsRendererCategory(statut, symbol, statut))
    if categories:
        layer.setRenderer(QgsCategorizedSymbolRenderer("statut", categories))


def _style_parcelles(layer):
    """Une teinte par intitule de culture, verte pour l'herbe.

    La categorisation porte sur le libelle et non sur le code : c'est
    "Prairie permanente - herbe predominante" que l'utilisateur veut lire
    dans son panneau des couches, pas "PPH". Les intitules sont classes par
    surface decroissante pour que la legende s'ouvre sur ce qui domine.

    Les parcelles sont opaques, a la difference des zonages : elles ne se
    superposent pas - une parcelle declaree l'est pour une seule culture - et
    la transparence ne servirait qu'a delaver la carte.
    """
    from qgis.core import (
        QgsCategorizedSymbolRenderer, QgsFillSymbol, QgsRendererCategory,
    )

    from .agriculture import palette

    surfaces = {}
    natures = {}
    for feature in layer.getFeatures():
        libelle = feature["culture"]
        surfaces[libelle] = surfaces.get(libelle, 0.0) + (
            feature["surface_ha"] or 0.0)
        natures[libelle] = feature["nature"]
    if not surfaces:
        return

    classes = sorted(surfaces, key=lambda nom: -surfaces[nom])
    couleurs = palette(
        [nom for nom in classes if natures.get(nom) == "herbe"],
        [nom for nom in classes if natures.get(nom) != "herbe"],
    )

    courts = unique_short_labels(classes)
    categories = []
    for libelle in classes:
        symbol = QgsFillSymbol.createSimple({
            "color": couleurs.get(libelle, "#999999"),
            "outline_color": "255,255,255,140",
            "outline_width": "0.15",
            "outline_style": "solid",
        })
        categories.append(
            QgsRendererCategory(libelle, symbol, courts[libelle]))
    layer.setRenderer(QgsCategorizedSymbolRenderer("culture", categories))
    # Legerement translucide : le fond de plan et le chevelu restent lisibles
    # sous la mosaique parcellaire, qui couvre parfois tout le bassin.
    layer.setOpacity(0.75)


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


# Rangement des couches dans le panneau, du dessus vers le dessous.
#
# (titre du sous-groupe ou None, cles des couches). Un titre nul range la
# couche directement sous le groupe du bassin : l'exutoire, le chevelu et le
# contour n'ont pas besoin d'un intitule pour se comprendre, la ou sept
# couches thematiques en vrac ne se retrouvent plus. Un sous-groupe qui n'a
# aucune couche a montrer n'est pas cree.
LAYER_GROUPS = (
    (None, ("exutoire",)),
    ("Hydrographie", ("obstacles", "reseau")),
    ("Zonages environnementaux", ("zonages",)),
    ("Agriculture", ("bio", "parcelles")),
    ("Occupation du sol", ("foret",)),
    (None, ("bassin",)),
)


def add_to_project(layers, group_name="BVLIP", iface=None, zoom=True):
    """Range les couches dans un groupe du projet et cadre la carte dessus.

    Les couches thematiques passent par des sous-groupes intitules. Sans eux,
    le panneau aligne sept couches de meme rang - parcelles, bio, formations,
    zonages, chevelu - et rien ne dit ce qui va avec quoi.
    """
    from qgis.core import QgsProject

    style_layers(layers)
    project = QgsProject.instance()
    group = project.layerTreeRoot().insertGroup(0, group_name)

    for title, keys in LAYER_GROUPS:
        presentes = [layers.get(key) for key in keys]
        presentes = [layer for layer in presentes if layer is not None]
        if not presentes:
            continue
        # Un sous-groupe qui ne contiendrait qu'une couche de son propre nom
        # n'apporte rien : "Zonages environnementaux" contenant "Zonages
        # environnementaux" se replie donc sur la couche seule.
        redondant = (len(presentes) == 1
                     and title is not None
                     and presentes[0].name() == title)
        cible = group.addGroup(title) if title and not redondant else group
        for layer in presentes:
            project.addMapLayer(layer, False)
            cible.addLayer(layer)

    if zoom and iface is not None:
        extent = layers["bassin"].extent()
        extent.grow(extent.width() * 0.1)
        iface.mapCanvas().setExtent(extent)
        iface.mapCanvas().refresh()
    return group
