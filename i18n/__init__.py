# -*- coding: utf-8 -*-
"""Traductions embarquees de BVLIP (FR / EN / ES / PT / DE).

Le plugin n'utilise pas les fichiers .qm de Qt : le dictionnaire ci-dessous
suffit pour un plugin de cette taille et evite une etape de compilation.
La langue par defaut suit celle de QGIS, et l'utilisateur peut la changer
a la volee depuis le panneau.
"""

LANGUAGES = [
    ("fr", "Français"),
    ("en", "English"),
    ("es", "Español"),
    ("pt", "Português"),
    ("de", "Deutsch"),
]

FALLBACK = "en"

TR = {
    # --- Titres et navigation --------------------------------------------
    "plugin_title": {
        "fr": "BVLIP - Bassin versant amont",
        "en": "BVLIP - Upstream watershed",
        "es": "BVLIP - Cuenca aguas arriba",
        "pt": "BVLIP - Bacia a montante",
        "de": "BVLIP - Einzugsgebiet oberhalb",
    },
    "menu_title": {
        "fr": "&BVLIP", "en": "&BVLIP", "es": "&BVLIP",
        "pt": "&BVLIP", "de": "&BVLIP",
    },
    "action_open": {
        "fr": "Ouvrir le panneau BVLIP",
        "en": "Open the BVLIP panel",
        "es": "Abrir el panel BVLIP",
        "pt": "Abrir o painel BVLIP",
        "de": "BVLIP-Bereich öffnen",
    },
    "action_tooltip": {
        "fr": "Délimiter le bassin versant en amont d'un point",
        "en": "Delineate the watershed upstream of a point",
        "es": "Delimitar la cuenca aguas arriba de un punto",
        "pt": "Delimitar a bacia a montante de um ponto",
        "de": "Einzugsgebiet oberhalb eines Punktes abgrenzen",
    },
    "menu_settings": {
        "fr": "Réglages...", "en": "Settings...", "es": "Ajustes...",
        "pt": "Definições...", "de": "Einstellungen...",
    },
    "settings_title": {
        "fr": "BVLIP - Réglages",
        "en": "BVLIP - Settings",
        "es": "BVLIP - Ajustes",
        "pt": "BVLIP - Definições",
        "de": "BVLIP - Einstellungen",
    },
    "group_snapping": {
        "fr": "Accrochage de l'exutoire",
        "en": "Outlet snapping",
        "es": "Ajuste del punto de salida",
        "pt": "Ajuste do exutório",
        "de": "Fang des Auslasses",
    },
    "about": {
        "fr": "À propos", "en": "About", "es": "Acerca de",
        "pt": "Acerca de", "de": "Über",
    },
    "language": {
        "fr": "Langue", "en": "Language", "es": "Idioma",
        "pt": "Idioma", "de": "Sprache",
    },

    # --- Exutoire ---------------------------------------------------------
    "group_outlet": {
        "fr": "Exutoire", "en": "Outlet", "es": "Punto de salida",
        "pt": "Exutório", "de": "Auslass",
    },
    "btn_pick": {
        "fr": "Cliquer un point sur la carte",
        "en": "Pick a point on the map",
        "es": "Seleccionar un punto en el mapa",
        "pt": "Selecionar um ponto no mapa",
        "de": "Punkt auf der Karte wählen",
    },
    "no_outlet": {
        "fr": "Aucun exutoire défini",
        "en": "No outlet defined",
        "es": "Ningún punto de salida definido",
        "pt": "Nenhum exutório definido",
        "de": "Kein Auslass definiert",
    },
    "outlet_set": {
        "fr": "Exutoire : {x:.1f} ; {y:.1f} (Lambert 93)",
        "en": "Outlet: {x:.1f} ; {y:.1f} (Lambert 93)",
        "es": "Punto de salida: {x:.1f} ; {y:.1f} (Lambert 93)",
        "pt": "Exutório: {x:.1f} ; {y:.1f} (Lambert 93)",
        "de": "Auslass: {x:.1f} ; {y:.1f} (Lambert 93)",
    },
    "thalweg_cells": {
        "fr": "Recalage sur le chevelu (m)",
        "en": "Re-snapping to the channel network (m)",
        "es": "Reajuste a la red de cauces (m)",
        "pt": "Reajuste a rede de canais (m)",
        "de": "Nachfang auf das Gerinnenetz (m)",
    },
    "thalweg_tip": {
        "fr": "Distance à laquelle chercher un chenal du modèle de terrain "
              "autour de l'exutoire. Le tracé cartographique d'un cours "
              "d'eau et le talweg calculé s'écartent couramment de plusieurs "
              "dizaines de mètres en fond de vallée.",
        "en": "How far to look for a channel of the terrain model around "
              "the outlet. A mapped watercourse and the computed thalweg "
              "commonly differ by tens of metres in valley bottoms.",
        "es": "Radio de búsqueda de la celda más drenada alrededor del punto "
              "de salida. 0 desactiva el reajuste.",
        "pt": "Raio de busca da célula mais drenada em torno do exutório. "
              "0 desativa o reajuste.",
        "de": "Suchradius für die am stärksten entwässerte Zelle um den "
              "Auslass. 0 schaltet den Nachfang ab.",
    },
    "snap_radius": {
        "fr": "Rayon d'accrochage au réseau (m)",
        "en": "Snapping radius to the network (m)",
        "es": "Radio de ajuste a la red (m)",
        "pt": "Raio de ajuste a rede (m)",
        "de": "Fangradius zum Netz (m)",
    },

    # --- Options ----------------------------------------------------------
    "group_options": {
        "fr": "Données à rapatrier",
        "en": "Data to retrieve",
        "es": "Datos a recuperar",
        "pt": "Dados a obter",
        "de": "Abzurufende Daten",
    },
    "btn_select_all": {
        "fr": "Tout cocher", "en": "Select all", "es": "Marcar todo",
        "pt": "Marcar tudo", "de": "Alle wählen",
    },
    "btn_select_none": {
        "fr": "Tout décocher", "en": "Clear all", "es": "Desmarcar todo",
        "pt": "Desmarcar tudo", "de": "Alle abwählen",
    },
    "datasets_count": {
        "fr": "{0} / {1} données",
        "en": "{0} / {1} datasets",
        "es": "{0} / {1} datos",
        "pt": "{0} / {1} dados",
        "de": "{0} / {1} Datensätze",
    },

    # --- Onglets du catalogue des donnees ---------------------------------
    "dstab_bassin": {
        "fr": "Bassin", "en": "Basin", "es": "Cuenca",
        "pt": "Bacia", "de": "Gebiet",
    },
    "dstab_sol": {
        "fr": "Sol", "en": "Land", "es": "Suelo",
        "pt": "Solo", "de": "Boden",
    },
    "dstab_agricole": {
        "fr": "Agricole", "en": "Farming", "es": "Agrario",
        "pt": "Agrícola", "de": "Landwirtschaft",
    },
    "dstab_zonages": {
        "fr": "Zonages", "en": "Designations", "es": "Zonificación",
        "pt": "Zonamentos", "de": "Schutzgebiete",
    },
    "dstab_eau": {
        "fr": "Eau", "en": "Water", "es": "Agua",
        "pt": "Água", "de": "Wasser",
    },

    # --- Donnees : onglet Bassin ------------------------------------------
    "ds_metriques": {
        "fr": "Métriques morphométriques",
        "en": "Morphometric metrics",
        "es": "Métricas morfométricas",
        "pt": "Métricas morfométricas",
        "de": "Morphometrische Kennwerte",
    },
    "ds_affinage": {
        "fr": "Recalculer à la maille la plus fine",
        "en": "Recompute at the finest cell size",
        "es": "Recalcular con la malla más fina",
        "pt": "Recalcular com a malha mais fina",
        "de": "Mit der feinsten Zellgröße neu berechnen",
    },

    # --- Donnees : onglet Sol ---------------------------------------------
    "ds_corine": {
        "fr": "Corine Land Cover 2018",
        "en": "Corine Land Cover 2018",
        "es": "Corine Land Cover 2018",
        "pt": "Corine Land Cover 2018",
        "de": "Corine Land Cover 2018",
    },
    "ds_bati": {
        "fr": "Bâti BD TOPO",
        "en": "BD TOPO buildings",
        "es": "Edificación BD TOPO",
        "pt": "Edificado BD TOPO",
        "de": "Bebauung BD TOPO",
    },
    "ds_foret": {
        "fr": "Couvert forestier BD Forêt v2",
        "en": "BD Forêt v2 forest cover",
        "es": "Cubierta forestal BD Forêt v2",
        "pt": "Coberto florestal BD Forêt v2",
        "de": "Waldbedeckung BD Forêt v2",
    },

    # --- Donnees : onglet Agricole ----------------------------------------
    "ds_rpg": {
        "fr": "Parcelles PAC (RPG)",
        "en": "CAP parcels (RPG)",
        "es": "Parcelas PAC (RPG)",
        "pt": "Parcelas PAC (RPG)",
        "de": "GAP-Schläge (RPG)",
    },
    "dsinfo_rpg": {
        "fr": "Registre parcellaire graphique : les parcelles déclarées "
              "chaque année par les exploitants au titre de la politique "
              "agricole commune. Surface déclarée dans le bassin, part de "
              "celui-ci, nombre et taille des parcelles, répartition entre "
              "terres arables, cultures permanentes et prairies, et le détail "
              "des cultures. Attention : le RPG ne couvre que le déclaré - un "
              "exploitant qui ne demande pas d'aide n'y figure pas. La "
              "surface obtenue minore la surface agricole réelle.",
        "en": "Graphic parcel register: the plots declared each year by "
              "farmers under the common agricultural policy. Declared area "
              "within the basin, its share, parcel count and size, split "
              "between arable land, permanent crops and grassland, and the "
              "crop detail. Mind that the register covers only what is "
              "declared - a farmer claiming no aid does not appear - so the "
              "area is a lower bound of the real farmland.",
        "es": "Registro parcelario gráfico : las parcelas declaradas cada "
              "año por los agricultores en el marco de la PAC. Superficie "
              "declarada, número y tamaño de parcelas, reparto entre tierras "
              "arables, cultivos permanentes y pastos. Solo cubre lo "
              "declarado : es un mínimo de la superficie agraria real.",
        "pt": "Registo parcelar gráfico : as parcelas declaradas todos os "
              "anos pelos agricultores no âmbito da PAC. Área declarada, "
              "número e dimensão das parcelas, repartição entre terras "
              "aráveis, culturas permanentes e prados. Só cobre o declarado : "
              "e um mínimo da área agrícola real.",
        "de": "Grafisches Schlagverzeichnis: die jährlich von den Betrieben "
              "im Rahmen der GAP gemeldeten Schläge. Gemeldete Fläche, Zahl "
              "und Größe der Schläge, Aufteilung in Ackerland, Dauerkulturen "
              "und Grünland. Erfasst nur Gemeldetes und ist daher eine "
              "Untergrenze der tatsächlichen Agrarfläche.",
    },
    "ds_bio": {
        "fr": "Agriculture biologique",
        "en": "Organic farming",
        "es": "Agricultura ecológica",
        "pt": "Agricultura biológica",
        "de": "Ökologischer Landbau",
    },
    "dsinfo_bio": {
        "fr": "Parcelles déclarées en agriculture biologique ou en cours de "
              "conversion, avec leur stade - certifiée, ou première, deuxième "
              "ou troisième année de conversion. Surface, part du bassin et "
              "part de la surface déclarée. Les engagements en mesures "
              "agroenvironnementales et climatiques, eux, ne sont pas publiés "
              "à la parcelle : c'est une donnée d'aide individuelle, et le "
              "bio est ce qui s'en approche le plus dans l'ouvert.",
        "en": "Plots declared under organic farming or in conversion, with "
              "their stage - certified, or first, second or third year of "
              "conversion. Area, share of the basin and share of the declared "
              "area. Agri-environmental scheme commitments are not published "
              "at plot level - they are individual aid data - and organic "
              "farming is the closest open substitute.",
        "es": "Parcelas declaradas en agricultura ecológica o en conversión, "
              "con su fase. Superficie, parte de la cuenca y de la superficie "
              "declarada. Los compromisos agroambientales no se publican por "
              "parcela : el ecológico es lo más cercano en datos abiertos.",
        "pt": "Parcelas declaradas em agricultura biológica ou em conversão, "
              "com a sua fase. Área, parte da bacia e da área declarada. Os "
              "compromissos agroambientais não são publicados a parcela : o "
              "biológico e o mais próximo nos dados abertos.",
        "de": "Als ökologisch oder in Umstellung gemeldete Schläge, mit ihrer "
              "Stufe. Fläche, Anteil am Gebiet und an der gemeldeten Fläche. "
              "Agrarumweltverpflichtungen werden nicht schlagbezogen "
              "veröffentlicht; der Ökolandbau kommt dem am nächsten.",
    },
    "ds_prairies": {
        "fr": "Prairies sensibles (BCAE)",
        "en": "Sensitive grassland (GAEC)",
        "es": "Pastos sensibles (BCAM)",
        "pt": "Prados sensíveis (BCAA)",
        "de": "Sensibles Dauergrünland (GLOZ)",
    },
    "dsinfo_prairies": {
        "fr": "Prairies et pâturages permanents situés en zone Natura 2000 "
              "et protégés au titre des bonnes conditions agricoles et "
              "environnementales : leur retournement est interdit. Leur "
              "intérêt ici est autant hydrologique qu'agricole - une prairie "
              "permanente retient l'eau et le sol là où un labour les laisse "
              "partir.",
        "en": "Permanent grassland and pasture inside Natura 2000 areas, "
              "protected under good agricultural and environmental "
              "conditions: ploughing them is forbidden. Their interest here "
              "is as much hydrological as agricultural - permanent grassland "
              "holds water and soil where tillage lets both go.",
        "es": "Pastos permanentes en zona Natura 2000, protegidos por las "
              "buenas condiciones agrarias y medioambientales : su laboreo "
              "está prohibido. Interés tanto hidrológico como agrario.",
        "pt": "Prados permanentes em zona Natura 2000, protegidos pelas boas "
              "condições agrícolas e ambientais : a lavoura e proibida. "
              "Interesse tanto hidrológico como agrícola.",
        "de": "Dauergrünland in Natura-2000-Gebieten, nach den GLOZ-"
              "Standards geschützt: Umbruch ist verboten. Ebenso "
              "hydrologisch wie landwirtschaftlich von Belang.",
    },
    "ds_aoc": {
        "fr": "Aires AOC viticoles",
        "en": "Wine PDO areas",
        "es": "Áreas DOP vitivinícolas",
        "pt": "Áreas DOP vitivinícolas",
        "de": "Weinbau-Ursprungsgebiete",
    },
    "dsinfo_aoc": {
        "fr": "Délimitation parcellaire des appellations d'origine "
              "contrôlée viticoles, établie par l'INAO. Surface classée dans "
              "le bassin et part de celui-ci. Ne rend rien là où il n'y a pas "
              "de vigne, ce qui est le cas de la plus grande partie du "
              "territoire.",
        "en": "Parcel-level delineation of wine protected designations of "
              "origin, set by the INAO. Classified area within the basin and "
              "its share. Returns nothing where there are no vines, which is "
              "most of the country.",
        "es": "Delimitación parcelaria de las denominaciones de origen "
              "vitivinícolas, establecida por el INAO. Superficie clasificada "
              "en la cuenca. Vacía allí donde no hay viña.",
        "pt": "Delimitação parcelar das denominações de origem vitivinícolas, "
              "estabelecida pelo INAO. Área classificada na bacia. Vazia onde "
              "não ha vinha.",
        "de": "Parzellenschärfe Abgrenzung der Weinbau-Ursprungs"
              "bezeichnungen des INAO. Ausgewiesene Fläche im Gebiet. Ohne "
              "Rebflächen bleibt sie leer.",
    },

    # --- Donnees : onglet Zonages -----------------------------------------
    "ds_znieff1": {
        "fr": "ZNIEFF de type I",
        "en": "ZNIEFF type I",
        "es": "ZNIEFF de tipo I",
        "pt": "ZNIEFF de tipo I",
        "de": "ZNIEFF Typ I",
    },
    "ds_znieff2": {
        "fr": "ZNIEFF de type II",
        "en": "ZNIEFF type II",
        "es": "ZNIEFF de tipo II",
        "pt": "ZNIEFF de tipo II",
        "de": "ZNIEFF Typ II",
    },
    "ds_zsc": {
        "fr": "Natura 2000 - ZSC (habitats)",
        "en": "Natura 2000 - SAC (habitats)",
        "es": "Natura 2000 - ZEC (habitats)",
        "pt": "Natura 2000 - ZEC (habitats)",
        "de": "Natura 2000 - FFH-Gebiet",
    },
    "ds_zps": {
        "fr": "Natura 2000 - ZPS (oiseaux)",
        "en": "Natura 2000 - SPA (birds)",
        "es": "Natura 2000 - ZEPA (aves)",
        "pt": "Natura 2000 - ZPE (aves)",
        "de": "Natura 2000 - Vogelschutzgebiet",
    },
    "ds_apb": {
        "fr": "Arrêté de protection de biotope",
        "en": "Biotope protection order",
        "es": "Orden de protección de biotopo",
        "pt": "Despacho de proteção de biotopo",
        "de": "Biotopschutzverordnung",
    },
    "ds_rnn": {
        "fr": "Réserve naturelle nationale",
        "en": "National nature reserve",
        "es": "Reserva natural nacional",
        "pt": "Reserva natural nacional",
        "de": "Nationales Naturschutzgebiet",
    },
    "ds_rnr": {
        "fr": "Réserve naturelle régionale",
        "en": "Regional nature reserve",
        "es": "Reserva natural regional",
        "pt": "Reserva natural regional",
        "de": "Regionales Naturschutzgebiet",
    },
    "ds_pnr": {
        "fr": "Parc naturel régional",
        "en": "Regional nature park",
        "es": "Parque natural regional",
        "pt": "Parque natural regional",
        "de": "Regionaler Naturpark",
    },
    "ds_ramsar": {
        "fr": "Site Ramsar",
        "en": "Ramsar site",
        "es": "Sitio Ramsar",
        "pt": "Sítio Ramsar",
        "de": "Ramsar-Gebiet",
    },
    "ds_zhumide": {
        "fr": "Zones humides et tourbières",
        "en": "Wetlands and peatlands",
        "es": "Humedales y turberas",
        "pt": "Zonas húmidas e turfeiras",
        "de": "Feuchtgebiete und Moore",
    },
    "ds_nitrate": {
        "fr": "Zone vulnérable aux nitrates",
        "en": "Nitrate vulnerable zone",
        "es": "Zona vulnerable a nitratos",
        "pt": "Zona vulnerável aos nitratos",
        "de": "Nitratgefährdetes Gebiet",
    },
    "ds_eutroph": {
        "fr": "Zone sensible à l'eutrophisation",
        "en": "Area sensitive to eutrophication",
        "es": "Zona sensible a la eutrofización",
        "pt": "Zona sensível a eutrofização",
        "de": "Eutrophierungsempfindliches Gebiet",
    },

    # --- Donnees : onglet Eau ---------------------------------------------
    "ds_masse_eau": {
        "fr": "Masse d'eau DCE de surface",
        "en": "WFD surface water body",
        "es": "Masa de agua superficial DMA",
        "pt": "Massa de água superficial DQA",
        "de": "WRRL-Oberflächenwasserkörper",
    },
    "ds_meso": {
        "fr": "Masse d'eau souterraine",
        "en": "Groundwater body",
        "es": "Masa de agua subterránea",
        "pt": "Massa de água subterrânea",
        "de": "Grundwasserkörper",
    },
    "ds_her": {
        "fr": "Hydroécorégions 1 et 2",
        "en": "Hydro-ecoregions 1 and 2",
        "es": "Hidroecorregiones 1 y 2",
        "pt": "Hidroecorregiões 1 e 2",
        "de": "Hydroökoregionen 1 und 2",
    },
    "ds_roe": {
        "fr": "Obstacles à l'écoulement (ROE)",
        "en": "Barriers to flow (ROE)",
        "es": "Obstáculos al flujo (ROE)",
        "pt": "Obstáculos ao escoamento (ROE)",
        "de": "Querbauwerke (ROE)",
    },
    "ds_steu": {
        "fr": "Stations de traitement (STEU)",
        "en": "Wastewater treatment plants",
        "es": "Estaciones depuradoras",
        "pt": "Estações de tratamento",
        "de": "Kläranlagen",
    },
    "ds_population": {
        "fr": "Population estimée",
        "en": "Estimated population",
        "es": "Población estimada",
        "pt": "População estimada",
        "de": "Geschätzte Bevölkerung",
    },
    "ds_prelevements": {
        "fr": "Prélèvements d'eau",
        "en": "Water withdrawals",
        "es": "Extracciones de agua",
        "pt": "Captações de água",
        "de": "Wasserentnahmen",
    },
    "ds_hydrometrie": {
        "fr": "Sites hydrométriques",
        "en": "Gauging sites",
        "es": "Estaciones de aforo",
        "pt": "Estações hidrométricas",
        "de": "Pegelstationen",
    },

    # --- Descriptions longues, au survol du i ------------------------------
    "dsinfo_metriques": {
        "fr": "Surface, périmètre, indice de compacité de Gravelius, "
              "rectangle équivalent, hypsométrie en neuf points, pentes "
              "moyenne et médiane, indice de pente global, dénivelée "
              "spécifique, plus long cheminement hydraulique et densité de "
              "drainage. Tout se calcule sur le modèle de terrain déjà "
              "télécharge : aucune requête de plus.",
        "en": "Area, perimeter, Gravelius compactness index, equivalent "
              "rectangle, nine-point hypsometry, mean and median slopes, "
              "global slope index, specific relief, longest flow path and "
              "drainage density. All computed on the elevation model already "
              "downloaded: no further request.",
        "es": "Superficie, perímetro, índice de Gravelius, rectángulo "
              "equivalente, hipsometría, pendientes, índice de pendiente "
              "global, desnivel específico, cauce más largo y densidad de "
              "drenaje. Se calcula sobre el MDT ya descargado.",
        "pt": "Área, perímetro, índice de Gravelius, retângulo equivalente, "
              "hipsometria, declives, índice de declive global, desnível "
              "específico, percurso mais longo e densidade de drenagem. "
              "Calculado sobre o MDT já descarregado.",
        "de": "Fläche, Umfang, Gravelius-Index, Äquivalentrechteck, "
              "Hypsometrie, Hangneigungen, globaler Neigungsindex, "
              "spezifisches Relief, längster Fließweg und Entwässerungs"
              "dichte. Alles aus dem bereits geladenen Höhenmodell.",
    },
    "dsinfo_affinage": {
        "fr": "Sur un grand bassin, la maille du modèle de terrain est "
              "élargie faute de mémoire. Cette option relance un second "
              "calcul sur le bassin recadré, ce qui permet de revenir à 5 m. "
              "Environ deux fois plus long, et sans effet sur la surface : "
              "n'a d'intérêt que si la pente ou le plus long cheminement "
              "comptent.",
        "en": "On a large catchment the cell size is enlarged for lack of "
              "memory. This option runs a second pass on the cropped basin, "
              "back down to 5 m. About twice as long, and it does not change "
              "the area: worth it only when slope or the longest flow path "
              "matter.",
        "es": "En una cuenca grande la malla se amplía por falta de memoria. "
              "Esta opción relanza un segundo cálculo sobre la cuenca "
              "recortada, hasta 5 m. Dura el doble y no cambia la superficie.",
        "pt": "Numa bacia grande a malha e alargada por falta de memória. "
              "Esta opção repete o cálculo sobre a bacia recortada, até 5 m. "
              "Demora o dobro e não altera a área.",
        "de": "Bei großen Gebieten wird die Zellgröße aus Speichermangel "
              "vergrößert. Diese Option rechnet ein zweites Mal auf dem "
              "zugeschnittenen Gebiet, zurück auf 5 m. Etwa doppelt so "
              "lange, ohne die Fläche zu ändern.",
    },

    "dsinfo_corine": {
        "fr": "Répartition de l'occupation du sol en quarante-quatre classes "
              "et cinq grands postes, avec la classe dominante et sa part. "
              "Millésime 2018. Unité minimale de collecte de 25 ha : les "
              "hameaux et les petits boisements n'y figurent pas, d'où le "
              "bâti de la BD TOPO et la BD Forêt à côté.",
        "en": "Land cover split into forty-four classes and five broad "
              "groups, with the dominant class and its share. 2018 vintage. "
              "25 ha minimum mapping unit: hamlets and small woods are "
              "absent, hence BD TOPO buildings and BD Forêt alongside.",
        "es": "Ocupación del suelo en cuarenta y cuatro clases y cinco "
              "grupos, con la clase dominante. Edición 2018, unidad mínima "
              "de 25 ha : las aldeas y los bosquetes no aparecen.",
        "pt": "Ocupação do solo em quarenta e quatro classes e cinco grupos, "
              "com a classe dominante. Edição 2018, unidade mínima de 25 ha : "
              "lugarejos e pequenos bosques não constam.",
        "de": "Landbedeckung in vierundvierzig Klassen und fünf Gruppen, mit "
              "der vorherrschenden Klasse. Stand 2018, Mindestkartierfläche "
              "25 ha: Weiler und kleine Wälder fehlen.",
    },
    "dsinfo_bati": {
        "fr": "Emprise au sol des bâtiments et surface des zones "
              "d'habitation, au mètre près, avec le nombre de bâtiments. "
              "Mesure indépendamment de Corine et jamais additionné à lui, "
              "ce qui compterait deux fois les mêmes surfaces. C'est l'étape "
              "la plus lourde sur un grand bassin : des dizaines de milliers "
              "de polygones.",
        "en": "Building footprints and settlement areas to the metre, with "
              "the building count. Measured independently of Corine and "
              "never added to it, which would count the same surfaces twice. "
              "The heaviest step on a large basin: tens of thousands of "
              "polygons.",
        "es": "Superficie construida y zonas de habitación al metro, con el "
              "número de edificios. Se mide aparte de Corine y nunca se suma "
              "a el. Es el paso más pesado en una cuenca grande.",
        "pt": "Área de implantação dos edifícios e zonas de habitação ao "
              "metro, com o número de edifícios. Medido a parte do Corine e "
              "nunca somado a ele. E a etapa mais pesada numa bacia grande.",
        "de": "Gebäudegrundflächen und Siedlungsflächen metergenau, mit "
              "Gebäudezahl. Unabhängig von Corine erhoben und nie dazu "
              "addiert. Der aufwändigste Schritt bei großen Gebieten.",
    },
    "dsinfo_foret": {
        "fr": "Couvert forestier par formation végétale, à 0,5 ha d'unité "
              "minimale, avec la part des feuillus, des conifères et des "
              "peuplements mixtes. Deux totaux distincts : le couvert, qui "
              "comprend landes et formations herbacées, et la surface boisée, "
              "qui ne retient que les peuplements.",
        "en": "Forest cover by vegetation formation, 0.5 ha minimum unit, "
              "with the share of broadleaved, coniferous and mixed stands. "
              "Two distinct totals: cover, which includes heaths and "
              "herbaceous formations, and wooded area, which keeps stands "
              "only.",
        "es": "Cubierta forestal por formación vegetal, unidad mínima de "
              "0,5 ha, con la parte de frondosas, coníferas y mixtas. Dos "
              "totales : la cubierta, que incluye landas, y la superficie "
              "arbolada, solo las masas.",
        "pt": "Coberto florestal por formação vegetal, unidade mínima de "
              "0,5 ha, com a parte de folhosas, resinosas e mistas. Dois "
              "totais : o coberto, que inclui landes, e a área arborizada, "
              "apenas os povoamentos.",
        "de": "Waldbedeckung nach Vegetationsformation, Mindestfläche "
              "0,5 ha, mit Anteil von Laub-, Nadel- und Mischbeständen. Zwei "
              "Summen: Bedeckung inklusive Heiden, und reine Waldfläche.",
    },

    "dsinfo_znieff1": {
        "fr": "Zone naturelle d'intérêt écologique, faunistique et "
              "floristique de type I : secteur de superficie limitée abritant "
              "des espèces ou des milieux rares. C'est un inventaire "
              "scientifique et non une protection : elle n'interdit rien, "
              "mais un aménagement devra justifier de l'ignorer. Surface dans "
              "le bassin, part de celui-ci, et le nom des sites.",
        "en": "Type I ZNIEFF: a limited area holding rare species or "
              "habitats. A scientific inventory, not a protection: it forbids "
              "nothing, but a development will have to justify ignoring it. "
              "Area within the basin, its share, and the site names.",
        "es": "ZNIEFF de tipo I : sector de superficie limitada con especies "
              "o medios raros. Es un inventario científico, no una "
              "protección. Superficie en la cuenca, parte y nombre de los "
              "sitios.",
        "pt": "ZNIEFF de tipo I : setor de superfície limitada com espécies "
              "ou meios raros. E um inventário científico, não uma proteção. "
              "Área na bacia, parte e nome dos sítios.",
        "de": "ZNIEFF Typ I: kleinräumiges Gebiet mit seltenen Arten oder "
              "Lebensräumen. Ein wissenschaftliches Inventar, kein Schutz. "
              "Fläche im Gebiet, Anteil und Namen der Standorte.",
    },
    "dsinfo_znieff2": {
        "fr": "ZNIEFF de type II : grand ensemble naturel riche et peu "
              "modifié, qui englobe le plus souvent plusieurs zones de type "
              "I. Les deux se superposent donc, et leurs surfaces ne "
              "s'additionnent pas. Inventaire scientifique, sans portée "
              "réglementaire.",
        "en": "Type II ZNIEFF: a large, rich and little-altered natural unit, "
              "usually enclosing several type I zones. The two therefore "
              "overlap and their areas do not add up. A scientific inventory, "
              "with no regulatory force.",
        "es": "ZNIEFF de tipo II : gran conjunto natural rico y poco "
              "modificado, que suele englobar varias zonas de tipo I. Ambas "
              "se superponen y sus superficies no se suman.",
        "pt": "ZNIEFF de tipo II : grande conjunto natural rico e pouco "
              "alterado, que engloba várias zonas de tipo I. As duas "
              "sobrepõem-se e as áreas não se somam.",
        "de": "ZNIEFF Typ II: großräumige, reiche und wenig veränderte "
              "Naturräume, die meist mehrere Typ-I-Zonen umfassen. Beide "
              "überlagern sich, ihre Flächen addieren sich nicht.",
    },
    "dsinfo_zsc": {
        "fr": "Zone spéciale de conservation du réseau Natura 2000, désignée "
              "au titre de la directive Habitats pour des milieux naturels ou "
              "des espèces d'intérêt communautaire. Protection réglementaire "
              "réelle : tout projet susceptible d'affecter le site relève de "
              "l'évaluation des incidences. Recouvre souvent une ZPS.",
        "en": "Natura 2000 Special Area of Conservation, designated under "
              "the Habitats Directive. A real regulatory protection: any "
              "project liable to affect the site falls under appropriate "
              "assessment. Often overlaps an SPA.",
        "es": "Zona especial de conservación de Natura 2000, designada por la "
              "directiva Habitats. Protección reglamentaria real : todo "
              "proyecto que pueda afectarla exige evaluación de impacto.",
        "pt": "Zona especial de conservação da rede Natura 2000, designada ao "
              "abrigo da diretiva Habitats. Proteção regulamentar real : "
              "qualquer projeto que a possa afetar exige avaliação.",
        "de": "Natura-2000-Gebiet nach der FFH-Richtlinie. Echter "
              "rechtlicher Schutz: jedes Vorhaben, das das Gebiet "
              "beeinträchtigen kann, unterliegt der Verträglichkeitsprüfung.",
    },
    "dsinfo_zps": {
        "fr": "Zone de protection spéciale du réseau Natura 2000, désignée au "
              "titre de la directive Oiseaux. Même portée réglementaire que "
              "la ZSC, mais un objet différent : les oiseaux sauvages et "
              "leurs habitats. Les deux se superposent fréquemment sur les "
              "mêmes vallées.",
        "en": "Natura 2000 Special Protection Area, designated under the "
              "Birds Directive. Same regulatory force as an SAC, different "
              "subject: wild birds and their habitats. The two frequently "
              "overlap on the same valleys.",
        "es": "Zona de especial protección para las aves de Natura 2000, "
              "directiva Aves. Misma fuerza reglamentaria que la ZEC, objeto "
              "distinto. Ambas se superponen a menudo.",
        "pt": "Zona de proteção especial da rede Natura 2000, diretiva Aves. "
              "Mesma força regulamentar que a ZEC, objeto diferente. As duas "
              "sobrepõem-se frequentemente.",
        "de": "Natura-2000-Vogelschutzgebiet nach der Vogelschutzrichtlinie. "
              "Gleiche Rechtswirkung wie ein FFH-Gebiet, anderer Gegenstand. "
              "Beide überlagern sich häufig.",
    },
    "dsinfo_apb": {
        "fr": "Arrêté préfectoral de protection de biotope : interdiction "
              "d'activités pouvant nuire à un milieu qui abrite une espèce "
              "protégée. Petites surfaces, souvent une portion de cours d'eau "
              "ou une tourbière, mais la protection y est stricte et "
              "opposable.",
        "en": "Prefectural biotope protection order: activities liable to "
              "harm a habitat sheltering a protected species are forbidden. "
              "Small areas, often a river reach or a peat bog, but the "
              "protection is strict and enforceable.",
        "es": "Orden prefectoral de protección de biotopo : prohibe las "
              "actividades que puedan dañar un medio con especies "
              "protegidas. Superficies pequeñas, protección estricta.",
        "pt": "Despacho de proteção de biotopo : proibe atividades que possam "
              "prejudicar um meio com espécies protegidas. Áreas pequenas, "
              "proteção estrita.",
        "de": "Biotopschutzverordnung: verbietet Tätigkeiten, die einen "
              "Lebensraum geschützter Arten schädigen können. Kleine "
              "Flächen, strenger und durchsetzbarer Schutz.",
    },
    "dsinfo_rnn": {
        "fr": "Réserve naturelle nationale : le niveau de protection le plus "
              "élevé après le cœur de parc national. Créée par décret, dotée "
              "d'un plan de gestion et d'un gestionnaire. Rare : beaucoup de "
              "bassins n'en comptent aucune, et la ligne reste alors vide.",
        "en": "National nature reserve: the highest level of protection "
              "after a national park core. Created by decree, with a "
              "management plan and a manager. Rare: many basins hold none, "
              "and the row then stays empty.",
        "es": "Reserva natural nacional : el nivel de protección más alto "
              "tras el núcleo de parque nacional. Rara : muchas cuencas no "
              "tienen ninguna.",
        "pt": "Reserva natural nacional : o nível de proteção mais elevado "
              "após o núcleo de parque nacional. Rara : muitas bacias não "
              "tem nenhuma.",
        "de": "Nationales Naturschutzgebiet: höchste Schutzstufe nach der "
              "Kernzone eines Nationalparks. Selten: viele Gebiete haben "
              "keines.",
    },
    "dsinfo_rnr": {
        "fr": "Réserve naturelle régionale, créée par le conseil régional. "
              "Même logique qu'une réserve nationale, à l'échelle de la "
              "région et souvent sur des surfaces plus modestes.",
        "en": "Regional nature reserve, created by the regional council. "
              "Same logic as a national reserve, at regional scale and often "
              "on smaller areas.",
        "es": "Reserva natural regional, creada por el consejo regional. "
              "Misma lógica que la nacional, a escala regional.",
        "pt": "Reserva natural regional, criada pelo conselho regional. "
              "Mesma lógica que a nacional, a escala regional.",
        "de": "Regionales Naturschutzgebiet, vom Regionalrat ausgewiesen. "
              "Gleiche Logik wie national, auf regionaler Ebene.",
    },
    "dsinfo_pnr": {
        "fr": "Parc naturel régional : territoire habité, classé pour la "
              "qualité de son patrimoine et géré par une charte. Ce n'est pas "
              "une protection réglementaire mais un projet de territoire, et "
              "les surfaces sont vastes - un parc couvre souvent tout un "
              "bassin versant.",
        "en": "Regional nature park: an inhabited territory classified for "
              "the quality of its heritage and run under a charter. Not a "
              "regulatory protection but a territorial project, and the areas "
              "are vast - a park often covers a whole catchment.",
        "es": "Parque natural regional : territorio habitado, clasificado por "
              "la calidad de su patrimonio y gestionado por una carta. No es "
              "una protección reglamentaria. Superficies muy amplias.",
        "pt": "Parque natural regional : território habitado, classificado "
              "pela qualidade do seu património e gerido por uma carta. Não e "
              "uma proteção regulamentar. Áreas muito vastas.",
        "de": "Regionaler Naturpark: besiedeltes Gebiet, wegen seines Erbes "
              "ausgewiesen und über eine Charta geführt. Kein rechtlicher "
              "Schutz, sondern ein Gebietsprojekt. Sehr große Flächen.",
    },
    "dsinfo_ramsar": {
        "fr": "Zone humide d'importance internationale au titre de la "
              "convention de Ramsar. Engagement de l'État plutôt que "
              "protection opposable, mais le classement signale une zone "
              "humide majeure, ce qui compte directement pour un bassin "
              "versant.",
        "en": "Wetland of international importance under the Ramsar "
              "convention. A state commitment rather than an enforceable "
              "protection, but the listing flags a major wetland, which "
              "matters directly for a catchment.",
        "es": "Humedal de importancia internacional (convenio de Ramsar). "
              "Compromiso del Estado más que protección oponible, pero señala "
              "un humedal importante.",
        "pt": "Zona húmida de importância internacional (convenção de "
              "Ramsar). Compromisso do Estado mais do que proteção oponível, "
              "mas assinala uma zona húmida importante.",
        "de": "Feuchtgebiet von internationaler Bedeutung (Ramsar-"
              "Konvention). Eher Staatsverpflichtung als durchsetzbarer "
              "Schutz, weist aber auf ein bedeutendes Feuchtgebiet hin.",
    },
    "dsinfo_zhumide": {
        "fr": "Zones humides et tourbières protégées au titre de la bonne "
              "condition agricole et environnementale n°2 de la politique "
              "agricole commune. Leur intérêt ici est hydrologique autant "
              "qu'écologique : ce sont les surfaces qui stockent et "
              "restituent l'eau.",
        "en": "Wetlands and peatlands protected under good agricultural and "
              "environmental condition 2 of the common agricultural policy. "
              "Their interest here is hydrological as much as ecological: "
              "these are the surfaces that store and release water.",
        "es": "Humedales y turberas protegidos por la condición agraria y "
              "medioambiental n°2 de la PAC. Su interés es hidrológico tanto "
              "como ecológico : almacenan y restituyen el agua.",
        "pt": "Zonas húmidas e turfeiras protegidas pela condição agrícola e "
              "ambiental n.2 da PAC. O interesse e hidrológico tanto quanto "
              "ecológico : armazenam e restituem a água.",
        "de": "Feuchtgebiete und Moore nach GLOZ-Standard 2 der Gemeinsamen "
              "Agrarpolitik. Hier ebenso hydrologisch wie ökologisch "
              "relevant: sie speichern und geben Wasser ab.",
    },
    "dsinfo_nitrate": {
        "fr": "Zone vulnérable aux nitrates d'origine agricole, délimitée au "
              "titre de la directive Nitrates. Ce zonage ne dit pas ce que le "
              "bassin a de remarquable mais ce qu'il subit : programme "
              "d'actions obligatoire pour les exploitations qui s'y trouvent.",
        "en": "Nitrate vulnerable zone under the Nitrates Directive. This "
              "designation says not what is remarkable about the basin but "
              "what it undergoes: a mandatory action programme applies to "
              "farms within it.",
        "es": "Zona vulnerable a los nitratos de origen agrario (directiva "
              "Nitratos). No dice lo que la cuenca tiene de notable sino lo "
              "que sufre : programa de actuación obligatorio.",
        "pt": "Zona vulnerável aos nitratos de origem agrícola (diretiva "
              "Nitratos). Não diz o que a bacia tem de notável mas o que "
              "sofre : programa de ação obrigatório.",
        "de": "Nitratgefährdetes Gebiet nach der Nitratrichtlinie. Sagt "
              "nicht, was am Gebiet bemerkenswert ist, sondern was es "
              "erleidet: verpflichtendes Aktionsprogramm für Betriebe.",
    },
    "dsinfo_eutroph": {
        "fr": "Zone sensible à l'eutrophisation au titre de la directive eaux "
              "résiduaires urbaines : le milieu y reçoit des rejets qu'il ne "
              "dilue pas assez, ce qui impose un traitement poussé de l'azote "
              "ou du phosphore aux stations d'épuration. Vaste : de grands "
              "bassins entiers sont classes.",
        "en": "Area sensitive to eutrophication under the urban waste water "
              "directive: the receiving water does not dilute discharges "
              "enough, requiring advanced nitrogen or phosphorus treatment at "
              "treatment plants. Vast: entire large basins are designated.",
        "es": "Zona sensible a la eutrofización (directiva de aguas "
              "residuales urbanas) : exige tratamiento avanzado de nitrógeno "
              "o fósforo. Muy extensa : cuencas enteras están clasificadas.",
        "pt": "Zona sensível a eutrofização (diretiva das águas residuais "
              "urbanas) : exige tratamento avançado de azoto ou fósforo. "
              "Muito vasta : bacias inteiras estão classificadas.",
        "de": "Eutrophierungsempfindliches Gebiet nach der "
              "Kommunalabwasserrichtlinie: erfordert weitergehende "
              "Stickstoff- oder Phosphorbehandlung. Sehr großflächig.",
    },

    "dsinfo_masse_eau": {
        "fr": "Masse d'eau de surface au sens de la directive cadre sur "
              "l'eau : code européen, dénomination, surface de son bassin "
              "versant spécifique et catégorie. Le rattachement se fait par "
              "l'exutoire et non par le bassin ; si le point tombe hors de "
              "tout polygone, la masse d'eau la plus proche à 250 m est "
              "retenue et le rapport le signale.",
        "en": "Surface water body under the Water Framework Directive: "
              "European code, name, area of its specific catchment and "
              "category. Attached through the outlet, not the basin; if the "
              "point falls outside every polygon, the nearest water body "
              "within 250 m is used and the report says so.",
        "es": "Masa de agua superficial (DMA) : código europeo, "
              "denominación, superficie de su cuenca y categoría. Se asigna "
              "por el punto de salida, no por la cuenca.",
        "pt": "Massa de água superficial (DQA) : código europeu, "
              "denominação, área da sua bacia e categoria. A ligação faz-se "
              "pelo exutório, não pela bacia.",
        "de": "Oberflächenwasserkörper nach WRRL: EU-Code, Bezeichnung, "
              "Fläche seines Teileinzugsgebiets und Kategorie. Zuordnung "
              "über den Auslass, nicht über das Gebiet.",
    },
    "dsinfo_meso": {
        "fr": "Masse d'eau souterraine sous l'exutoire : code, dénomination, "
              "nature de l'écoulement, caractère karstique et surface "
              "d'affleurement. Les nappes se superposent ; c'est celle qui "
              "affleure qui est retenue, parce que c'est elle qui échange "
              "avec le cours d'eau. Un bassin topographique ne coïncide pas "
              "avec son bassin hydrogéologique.",
        "en": "Groundwater body under the outlet: code, name, flow type, "
              "karstic character and outcrop area. Aquifers overlap; the "
              "outcropping one is kept, being the one that exchanges with the "
              "stream. A topographic basin does not coincide with its "
              "hydrogeological one.",
        "es": "Masa de agua subterránea bajo el punto de salida : código, "
              "denominación, naturaleza del flujo, carácter kárstico y "
              "superficie aflorante. Se retiene la que aflora.",
        "pt": "Massa de água subterrânea sob o exutório : código, "
              "denominação, natureza do escoamento, carácter cársico e área "
              "aflorante. Retém-se a que aflora.",
        "de": "Grundwasserkörper unter dem Auslass: Code, Bezeichnung, "
              "Fließart, Verkarstung und Ausstrichfläche. Genommen wird der "
              "ausstreichende Körper.",
    },
    "dsinfo_her": {
        "fr": "Hydroécorégions de niveau 1 et 2 : le découpage qui sert de "
              "cadre de comparaison à la directive cadre sur l'eau. Les "
              "valeurs de référence d'un cours d'eau y sont établies, et deux "
              "bassins d'hydroécorégions différentes ne se comparent pas. "
              "Deux lectures ponctuelles, quasiment gratuites.",
        "en": "Hydro-ecoregions levels 1 and 2: the framework the Water "
              "Framework Directive compares against. Reference values for a "
              "watercourse are set within them, and two basins from different "
              "hydro-ecoregions do not compare. Two point lookups, almost "
              "free.",
        "es": "Hidroecorregiones de nivel 1 y 2 : el marco de comparación de "
              "la DMA. Dos cuencas de hidroecorregiones distintas no se "
              "comparan. Coste de cálculo casi nulo.",
        "pt": "Hidroecorregiões de nível 1 e 2 : o quadro de comparação da "
              "DQA. Duas bacias de hidroecorregiões diferentes não se "
              "comparam. Custo de cálculo quase nulo.",
        "de": "Hydroökoregionen der Ebenen 1 und 2: der Vergleichsrahmen der "
              "WRRL. Zwei Gebiete aus verschiedenen Hydroökoregionen sind "
              "nicht vergleichbar. Nahezu kostenlos.",
    },
    "dsinfo_steu": {
        "fr": "Stations de traitement des eaux usées implantées dans le "
              "bassin (Sandre) : capacité nominale en équivalent-habitants, "
              "charge entrante et taux de charge, autosurveillance et sa "
              "conformité, zone sensible de rejet. La taille du point suit "
              "la capacité. Les normes de rejet ne sont pas rapatriées — "
              "aucune base ouverte ne les donne station par station — mais "
              "calculées d'après l'arrêté du 21 juillet 2015 à partir de la "
              "capacité et de la zone sensible : ce sont les seuils "
              "réglementaires applicables, que l'arrêté préfectoral de "
              "l'ouvrage peut resserrer.",
        "en": "Wastewater treatment plants located in the basin (Sandre): "
              "nominal capacity in population equivalent, incoming load and "
              "load rate, self-monitoring and its compliance, sensitive "
              "discharge zone. Point size follows capacity. Discharge "
              "standards are not downloaded — no open database gives them "
              "plant by plant — but computed from the decree of 21 July 2015 "
              "using capacity and sensitive zone: these are the applicable "
              "regulatory thresholds, which the plant's prefectoral order "
              "may tighten.",
        "es": "Estaciones depuradoras situadas en la cuenca (Sandre): "
              "capacidad nominal en habitantes equivalentes, carga entrante "
              "y tasa de carga, autocontrol y su conformidad, zona sensible "
              "de vertido. El tamaño del punto sigue la capacidad. Los "
              "límites de vertido no se descargan — ninguna base abierta los "
              "da por estación — sino que se calculan según el decreto del "
              "21 de julio de 2015: son los umbrales reglamentarios "
              "aplicables, que la autorización prefectoral puede endurecer.",
        "pt": "Estações de tratamento de águas residuais na bacia (Sandre): "
              "capacidade nominal em equivalente-habitante, carga afluente e "
              "taxa de carga, autocontrolo e a sua conformidade, zona "
              "sensível de descarga. O tamanho do ponto segue a capacidade. "
              "Os limites de descarga não são descarregados — nenhuma base "
              "aberta os fornece por estação — mas calculados a partir do "
              "decreto de 21 de julho de 2015: são os limiares "
              "regulamentares aplicáveis, que a autorização pode restringir.",
        "de": "Kläranlagen im Einzugsgebiet (Sandre): Nennkapazität in "
              "Einwohnerwerten, Zulauffracht und Auslastung, Eigenkontrolle "
              "und deren Konformität, empfindliches Einleitgebiet. Die "
              "Punktgröße folgt der Kapazität. Die Einleitgrenzwerte werden "
              "nicht heruntergeladen — keine offene Datenbank liefert sie "
              "je Anlage — sondern nach dem Erlass vom 21. Juli 2015 aus "
              "Kapazität und empfindlichem Gebiet berechnet: es sind die "
              "geltenden Mindestanforderungen, die der behördliche "
              "Bescheid verschärfen kann.",
    },
    "dsinfo_population": {
        "fr": "Estimation de la population du bassin, par commune ADMIN "
              "EXPRESS (IGN) recoupant le bassin : les logements du bâti BD "
              "TOPO dans la part du bassin qui touche la commune, rapportés "
              "aux logements de la commune entière, appliqués à sa "
              "population officielle. N'est pas un recensement — une "
              "estimation qui suppose la densité de logements comparable "
              "dans et hors bassin.",
        "en": "Population estimate for the basin, commune by commune from "
              "ADMIN EXPRESS (IGN) intersecting it: BD TOPO building "
              "dwellings in the part of the basin touching the commune, "
              "against the whole commune's dwellings, applied to its "
              "official population. Not a census — an estimate assuming "
              "comparable dwelling density inside and outside the basin.",
        "es": "Estimación de la población de la cuenca, municipio por "
              "municipio ADMIN EXPRESS (IGN) que la corta: las viviendas del "
              "catastro BD TOPO en la parte de la cuenca que toca el "
              "municipio, frente a las viviendas de todo el municipio, "
              "aplicadas a su población oficial. No es un censo — una "
              "estimación que supone una densidad de viviendas comparable "
              "dentro y fuera de la cuenca.",
        "pt": "Estimativa da população da bacia, por município ADMIN "
              "EXPRESS (IGN) que a intersecta: as habitações do edificado "
              "BD TOPO na parte da bacia que toca o município, face às "
              "habitações de todo o município, aplicadas à sua população "
              "oficial. Não é um recenseamento — uma estimativa que "
              "pressupõe densidade de habitações comparável dentro e fora "
              "da bacia.",
        "de": "Bevölkerungsschätzung des Einzugsgebiets, Gemeinde für "
              "Gemeinde aus ADMIN EXPRESS (IGN), die es schneiden: die "
              "BD-TOPO-Gebäudewohnungen im Teil des Einzugsgebiets, der die "
              "Gemeinde berührt, im Verhältnis zu den Wohnungen der ganzen "
              "Gemeinde, angewandt auf deren offizielle Bevölkerung. Keine "
              "Volkszählung — eine Schätzung, die eine vergleichbare "
              "Wohnungsdichte innerhalb und außerhalb des Einzugsgebiets "
              "voraussetzt.",
    },
    "dsinfo_prelevements": {
        "fr": "Ouvrages de prélèvement d'eau recensés dans les communes "
              "recoupant le bassin (Hub'Eau / BNPE), retenus quand leur point "
              "tombe réellement dans le bassin : volume annuel prélevé pour "
              "le dernier exercice connu, par usage — eau potable, "
              "irrigation, industrie, énergie. Mesure la pression en amont, "
              "là où les STEU mesurent ce qui est rendu en aval.",
        "en": "Water withdrawal facilities recorded in communes intersecting "
              "the basin (Hub'Eau / BNPE), kept when their point actually "
              "falls inside the basin: annual volume withdrawn for the "
              "latest known year, by usage — drinking water, irrigation, "
              "industry, energy. Measures upstream pressure, where "
              "wastewater plants measure what is returned downstream.",
        "es": "Instalaciones de extracción de agua registradas en los "
              "municipios que cortan la cuenca (Hub'Eau / BNPE), retenidas "
              "cuando su punto cae realmente dentro de la cuenca: volumen "
              "anual extraído en el último ejercicio conocido, por uso — "
              "agua potable, riego, industria, energía. Mide la presión "
              "aguas arriba, donde las depuradoras miden lo devuelto aguas "
              "abajo.",
        "pt": "Captações de água registadas nos municípios que intersectam "
              "a bacia (Hub'Eau / BNPE), mantidas quando o seu ponto cai "
              "realmente dentro da bacia: volume anual captado no último "
              "ano conhecido, por uso — água potável, rega, indústria, "
              "energia. Mede a pressão a montante, onde as ETAR medem o que "
              "é devolvido a jusante.",
        "de": "In den das Einzugsgebiet schneidenden Gemeinden erfasste "
              "Wasserentnahmestellen (Hub'Eau / BNPE), berücksichtigt, wenn "
              "ihr Punkt tatsächlich im Einzugsgebiet liegt: jährlich "
              "entnommenes Volumen für das letzte bekannte Jahr, nach "
              "Nutzung — Trinkwasser, Bewässerung, Industrie, Energie. Misst "
              "den Druck stromaufwärts, während Kläranlagen messen, was "
              "stromabwärts zurückgegeben wird.",
    },
    "dsinfo_roe": {
        "fr": "Référentiel des obstacles à l'écoulement : barrages, seuils, "
              "digues recensés dans le bassin, avec leur nombre, ceux encore "
              "existants, ceux classes Grenelle, ceux équipes d'une passe à "
              "poissons, la hauteur de chute cumulée et la densité au "
              "kilomètre. La hauteur est reconstituée : le référentiel ne "
              "donne souvent qu'une classe, dont le milieu est retenu, et la "
              "somme est donc un minorant.",
        "en": "Register of barriers to flow: dams, weirs and dykes recorded "
              "in the basin, with their count, those still standing, those "
              "listed under the Grenelle, those with a fish pass, the "
              "cumulated head and the density per kilometre. Head is "
              "reconstructed: the register often gives only a class, whose "
              "midpoint is used, so the sum is a lower bound.",
        "es": "Registro de obstáculos al flujo : presas, azudes y diques de "
              "la cuenca, con su número, los que tienen escala de peces, la "
              "altura de caída acumulada y la densidad por kilómetro. La "
              "altura se reconstruye a partir de clases : es un mínimo.",
        "pt": "Registo de obstáculos ao escoamento : barragens, açudes e "
              "diques da bacia, com o número, os que tem passagem para "
              "peixes, a altura de queda acumulada e a densidade por "
              "quilómetro. A altura e reconstituída : e um mínimo.",
        "de": "Querbauwerksverzeichnis: Wehre, Dämme und Sperren im Gebiet, "
              "mit Anzahl, Fischaufstiegen, kumulierter Fallhöhe und Dichte "
              "je Kilometer. Die Fallhöhe wird aus Klassen rekonstruiert und "
              "ist daher eine Untergrenze.",
    },
    "dsinfo_hydrometrie": {
        "fr": "Sites hydrométriques du Sandre situés dans le bassin, avec "
              "leur code et leur gestionnaire. La question à laquelle ils "
              "répondent est simple et se pose toujours : le bassin est-il "
              "jauge, ou faudra-t-il reconstituer ses débits ? Un zéro est "
              "une réponse, pas une absence de donnée.",
        "en": "Sandre gauging sites inside the basin, with their code and "
              "operator. The question they answer is simple and always "
              "arises: is the basin gauged, or will its flows have to be "
              "reconstructed? A zero is an answer, not missing data.",
        "es": "Estaciones de aforo del Sandre en la cuenca, con su código y "
              "gestor. Responden a una pregunta simple : la cuenca está "
              "aforada ? Un cero es una respuesta, no un dato ausente.",
        "pt": "Estações hidrométricas do Sandre na bacia, com código e "
              "gestor. Respondem a uma pergunta simples : a bacia e medida ? "
              "Um zero e uma resposta, não um dado em falta.",
        "de": "Sandre-Pegelstationen im Gebiet, mit Code und Betreiber. Sie "
              "beantworten eine einfache Frage: ist das Gebiet bepegelt? "
              "Eine Null ist eine Antwort, kein fehlender Wert.",
    },

    # --- Execution --------------------------------------------------------
    "btn_report": {
        "fr": "Produire le rapport A4",
        "en": "Produce the A4 report",
        "es": "Generar el informe A4",
        "pt": "Gerar o relatório A4",
        "de": "A4-Bericht erzeugen",
    },
    "report_tip": {
        "fr": "Disponible une fois un bassin versant délimité.",
        "en": "Available once a watershed has been delineated.",
        "es": "Disponible tras delimitar una cuenca.",
        "pt": "Disponível após delimitar uma bacia.",
        "de": "Verfügbar, sobald ein Einzugsgebiet abgegrenzt ist.",
    },
    "btn_view3d": {
        "fr": "Aperçu 3D du relief",
        "en": "3D relief preview",
        "es": "Vista 3D del relieve",
        "pt": "Pré-visualização 3D do relevo",
        "de": "3D-Vorschau des Reliefs",
    },
    "view3d_tip": {
        "fr": "Bloc-diagramme du bassin, orienté à la souris. Disponible une "
              "fois un bassin délimité.",
        "en": "Block diagram of the catchment, rotated with the mouse. "
              "Available once a watershed has been delineated.",
        "es": "Bloque diagrama de la cuenca, girado con el ratón. Disponible "
              "tras delimitar una cuenca.",
        "pt": "Bloco-diagrama da bacia, rodado com o rato. Disponível após "
              "delimitar uma bacia.",
        "de": "Blockbild des Einzugsgebiets, mit der Maus drehbar. Verfügbar, "
              "sobald ein Einzugsgebiet abgegrenzt ist.",
    },
    "view3d_hint": {
        "fr": "Cliquer-glisser pour tourner, molette pour zoomer. Le relief "
              "est exagéré pour se voir.",
        "en": "Click and drag to rotate, wheel to zoom. Relief is exaggerated "
              "so that it shows.",
        "es": "Arrastrar para girar, rueda para ampliar. El relieve está "
              "exagerado para verse.",
        "pt": "Arrastar para rodar, roda para ampliar. O relevo está exagerado "
              "para se ver.",
        "de": "Ziehen zum Drehen, Rad zum Zoomen. Das Relief ist überhöht, "
              "damit es sichtbar wird.",
    },
    "view3d_sw": {
        "fr": "Vue du sud-ouest",
        "en": "From the south-west",
        "es": "Desde el suroeste",
        "pt": "De sudoeste",
        "de": "Von Südwesten",
    },
    "view3d_top": {
        "fr": "Vue du dessus",
        "en": "From above",
        "es": "Desde arriba",
        "pt": "De cima",
        "de": "Von oben",
    },
    "view3d_se": {
        "fr": "Vue du sud-est",
        "en": "From the south-east",
        "es": "Desde el sureste",
        "pt": "De sudeste",
        "de": "Von Südosten",
    },
    "view3d_ne": {
        "fr": "Vue du nord-est",
        "en": "From the north-east",
        "es": "Desde el noreste",
        "pt": "De nordeste",
        "de": "Von Nordosten",
    },
    "view3d_nw": {
        "fr": "Vue du nord-ouest",
        "en": "From the north-west",
        "es": "Desde el noroeste",
        "pt": "De noroeste",
        "de": "Von Nordwesten",
    },
    "view3d_exaggeration": {
        "fr": "Exagération verticale",
        "en": "Vertical exaggeration",
        "es": "Exageración vertical",
        "pt": "Exagero vertical",
        "de": "Überhöhung",
    },
    "view3d_export": {
        "fr": "Exporter l'image…",
        "en": "Export image…",
        "es": "Exportar imagen…",
        "pt": "Exportar imagem…",
        "de": "Bild exportieren…",
    },
    "view3d_export_mesh": {
        "fr": "Exporter le maillage (.glb)…",
        "en": "Export mesh (.glb)…",
        "es": "Exportar malla (.glb)…",
        "pt": "Exportar malha (.glb)…",
        "de": "Netz exportieren (.glb)…",
    },
    "view3d_view_group": {
        "fr": "Vue",
        "en": "View",
        "es": "Vista",
        "pt": "Vista",
        "de": "Ansicht",
    },
    "view3d_export_group": {
        "fr": "Export",
        "en": "Export",
        "es": "Exportar",
        "pt": "Exportar",
        "de": "Export",
    },
    "view3d_nw_short": {
        "fr": "NO", "en": "NW", "es": "NO", "pt": "NO", "de": "NW",
    },
    "view3d_ne_short": {
        "fr": "NE", "en": "NE", "es": "NE", "pt": "NE", "de": "NO",
    },
    "view3d_sw_short": {
        "fr": "SO", "en": "SW", "es": "SO", "pt": "SO", "de": "SW",
    },
    "view3d_se_short": {
        "fr": "SE", "en": "SE", "es": "SE", "pt": "SE", "de": "SO",
    },
    "view3d_top_short": {
        "fr": "Dessus",
        "en": "Top",
        "es": "Arriba",
        "pt": "Cima",
        "de": "Oben",
    },
    "view3d_legend_title": {
        "fr": "Légende",
        "en": "Legend",
        "es": "Leyenda",
        "pt": "Legenda",
        "de": "Legende",
    },
    "view3d_definition": {
        "fr": "Définition",
        "en": "Definition",
        "es": "Definición",
        "pt": "Definição",
        "de": "Auflösung",
    },
    "view3d_zoom_in": {
        "fr": "Zoom +", "en": "Zoom +", "es": "Zoom +", "pt": "Zoom +",
        "de": "Zoom +",
    },
    "view3d_zoom_out": {
        "fr": "Zoom −", "en": "Zoom −", "es": "Zoom −", "pt": "Zoom −",
        "de": "Zoom −",
    },
    "view3d_habillage": {
        "fr": "Habillage",
        "en": "Draping",
        "es": "Vestimenta",
        "pt": "Revestimento",
        "de": "Textur",
    },
    "view3d_habillage_reseau": {
        "fr": "Cours d'eau",
        "en": "Streams",
        "es": "Cursos de agua",
        "pt": "Cursos de água",
        "de": "Wasserläufe",
    },
    "view3d_habillage_agriculture": {
        "fr": "Agriculture (PAC)",
        "en": "Farming (CAP)",
        "es": "Agricultura (PAC)",
        "pt": "Agricultura (PAC)",
        "de": "Landwirtschaft (GAP)",
    },
    "view3d_habillage_foret": {
        "fr": "BD Forêt",
        "en": "BD Forêt (forest cover)",
        "es": "BD Forêt (cubierta forestal)",
        "pt": "BD Forêt (cobertura florestal)",
        "de": "BD Forêt (Waldbedeckung)",
    },
    "view3d_habillage_relief_gris": {
        "fr": "Relief (niveaux de gris)",
        "en": "Relief (greyscale)",
        "es": "Relieve (escala de grises)",
        "pt": "Relevo (tons de cinzento)",
        "de": "Relief (Graustufen)",
    },
    "view3d_move_up": {
        "fr": "Monter", "en": "Up", "es": "Subir", "pt": "Subir",
        "de": "Hoch",
    },
    "view3d_move_down": {
        "fr": "Descendre", "en": "Down", "es": "Bajar", "pt": "Descer",
        "de": "Runter",
    },
    "view3d_move_up_tip": {
        "fr": "Remonter l'habillage dans la pile (il recouvre les autres).",
        "en": "Move the draping up the stack (it covers the others).",
        "es": "Subir la capa en la pila (cubre a las demás).",
        "pt": "Subir a camada na pilha (cobre as outras).",
        "de": "Textur im Stapel nach oben (überdeckt die anderen).",
    },
    "view3d_move_down_tip": {
        "fr": "Descendre l'habillage dans la pile (les autres le recouvrent).",
        "en": "Move the draping down the stack (the others cover it).",
        "es": "Bajar la capa en la pila (las demás la cubren).",
        "pt": "Descer a camada na pilha (as outras cobrem-na).",
        "de": "Textur im Stapel nach unten (die anderen überdecken sie).",
    },
    "view3d_opacity": {
        "fr": "Opacité",
        "en": "Opacity",
        "es": "Opacidad",
        "pt": "Opacidade",
        "de": "Deckkraft",
    },
    "view3d_habillage_corine": {
        "fr": "Occupation du sol (Corine)",
        "en": "Land cover (Corine)",
        "es": "Uso del suelo (Corine)",
        "pt": "Uso do solo (Corine)",
        "de": "Bodenbedeckung (Corine)",
    },
    "view3d_habillage_loading": {
        "fr": "Chargement de l'habillage…",
        "en": "Loading draping…",
        "es": "Cargando la vestimenta…",
        "pt": "A carregar o revestimento…",
        "de": "Textur wird geladen…",
    },
    "view3d_habillage_error": {
        "fr": "Habillage indisponible : {error}",
        "en": "Draping unavailable: {error}",
        "es": "Vestimenta no disponible: {error}",
        "pt": "Revestimento indisponível: {error}",
        "de": "Textur nicht verfügbar: {error}",
    },
    "view3d_export_done": {
        "fr": "Enregistré : {path}",
        "en": "Saved: {path}",
        "es": "Guardado: {path}",
        "pt": "Guardado: {path}",
        "de": "Gespeichert: {path}",
    },
    "view3d_missing": {
        "fr": "Relief indisponible : matplotlib est absent, ou le calcul n'a "
              "pas conservé les altitudes.",
        "en": "Relief unavailable: matplotlib is missing, or the run did not "
              "keep the elevations.",
        "es": "Relieve no disponible: falta matplotlib, o el cálculo no "
              "conservó las altitudes.",
        "pt": "Relevo indisponível: falta o matplotlib, ou o cálculo não "
              "guardou as altitudes.",
        "de": "Relief nicht verfügbar: matplotlib fehlt, oder die Berechnung "
              "hat die Höhen nicht behalten.",
    },
    "preview_export": {
        "fr": "Exporter en PDF",
        "en": "Export to PDF",
        "es": "Exportar a PDF",
        "pt": "Exportar para PDF",
        "de": "Als PDF exportieren",
    },
    "btn_preview": {
        "fr": "Aperçu et impression",
        "en": "Preview and print",
        "es": "Vista previa e impresión",
        "pt": "Pré-visualizar e imprimir",
        "de": "Vorschau und Druck",
    },
    "preview_tip": {
        "fr": "Affiche la page A4 sans rien enregistrer : on regarde, on "
              "imprime, ou on ferme.",
        "en": "Shows the A4 page without saving anything: look at it, print "
              "it, or close it.",
        "es": "Muestra la página A4 sin guardar nada: mirar, imprimir o "
              "cerrar.",
        "pt": "Mostra a página A4 sem gravar nada: ver, imprimir ou fechar.",
        "de": "Zeigt die A4-Seite, ohne etwas zu speichern: ansehen, drucken "
              "oder schließen.",
    },
    "report_dialog": {
        "fr": "Enregistrer le rapport",
        "en": "Save the report",
        "es": "Guardar el informe",
        "pt": "Guardar o relatório",
        "de": "Bericht speichern",
    },
    "report_done": {
        "fr": "✔ Rapport écrit : {path}",
        "en": "✔ Report written: {path}",
        "es": "✔ Informe escrito: {path}",
        "pt": "✔ Relatório gravado: {path}",
        "de": "✔ Bericht gespeichert: {path}",
    },
    "report_xlsx": {
        "fr": "ℹ Classeur Excel : {path}",
        "en": "ℹ Excel workbook: {path}",
        "es": "ℹ Libro de Excel: {path}",
        "pt": "ℹ Livro Excel: {path}",
        "de": "ℹ Excel-Arbeitsmappe: {path}",
    },
    "report_ready_title": {
        "fr": "Rapport produit",
        "en": "Report produced",
        "es": "Informe generado",
        "pt": "Relatório gerado",
        "de": "Bericht erzeugt",
    },
    # Tient sur une ligne : le texte va dans un bandeau de la barre de
    # messages de QGIS, ou une question et des sauts de ligne n'ont plus lieu
    # d'etre - le bouton du bandeau pose la question a lui seul.
    "open_folder_ask": {
        "fr": "Rapport enregistré : {files}",
        "en": "Report saved: {files}",
        "es": "Informe guardado: {files}",
        "pt": "Relatório gravado: {files}",
        "de": "Bericht gespeichert: {files}",
    },
    "open_folder": {
        "fr": "Ouvrir le dossier",
        "en": "Open the folder",
        "es": "Abrir la carpeta",
        "pt": "Abrir a pasta",
        "de": "Ordner öffnen",
    },
    "open_folder_failed": {
        "fr": "⚠ Ouverture du dossier impossible : {path}",
        "en": "⚠ Could not open the folder: {path}",
        "es": "⚠ No se pudo abrir la carpeta: {path}",
        "pt": "⚠ Não foi possível abrir a pasta: {path}",
        "de": "⚠ Ordner könnte nicht geöffnet werden: {path}",
    },
    "no_workbook": {
        "fr": "⚠ openpyxl est absent : seul le PDF est produit.",
        "en": "⚠ openpyxl is missing: only the PDF is produced.",
        "es": "⚠ falta openpyxl: solo se genera el PDF.",
        "pt": "⚠ openpyxl ausente: apenas o PDF e gerado.",
        "de": "⚠ openpyxl fehlt: nur das PDF wird erzeugt.",
    },
    "no_charts": {
        "fr": "⚠ matplotlib est absent : rapport produit sans les graphiques.",
        "en": "⚠ matplotlib is missing: report produced without charts.",
        "es": "⚠ falta matplotlib: informe generado sin gráficos.",
        "pt": "⚠ matplotlib ausente: relatório gerado sem gráficos.",
        "de": "⚠ matplotlib fehlt: Bericht ohne Diagramme erzeugt.",
    },
    "layers_added": {
        "fr": "ℹ Couches créées en mémoire dans le groupe {group}.",
        "en": "ℹ Memory layers created in group {group}.",
        "es": "ℹ Capas en memoria creadas en el grupo {group}.",
        "pt": "ℹ Camadas em memória criadas no grupo {group}.",
        "de": "ℹ Speicherlayer in Gruppe {group} erstellt.",
    },
    "btn_run": {
        "fr": "Délimiter le bassin versant",
        "en": "Delineate the watershed",
        "es": "Delimitar la cuenca",
        "pt": "Delimitar a bacia",
        "de": "Einzugsgebiet abgrenzen",
    },
    "btn_cancel": {
        "fr": "Annuler le calcul",
        "en": "Cancel the computation",
        "es": "Cancelar el cálculo",
        "pt": "Cancelar o cálculo",
        "de": "Berechnung abbrechen",
    },
    "cancelled": {
        "fr": "Calcul annulé.",
        "en": "Computation cancelled.",
        "es": "Cálculo cancelado.",
        "pt": "Cálculo cancelado.",
        "de": "Berechnung abgebrochen.",
    },
    "running_background": {
        "fr": "Calcul en cours en arrière-plan : QGIS reste utilisable.",
        "en": "Running in the background: QGIS stays usable.",
        "es": "Cálculo en segundo plano: QGIS sigue utilizable.",
        "pt": "Cálculo em segundo plano: o QGIS continua utilizável.",
        "de": "Berechnung im Hintergrund: QGIS bleibt bedienbar.",
    },
    "ready": {
        "fr": "Prêt.", "en": "Ready.", "es": "Listo.",
        "pt": "Pronto.", "de": "Bereit.",
    },
    "progress_fmt": {
        "fr": "%v / %m étape(s)", "en": "%v / %m step(s)",
        "es": "%v / %m etapa(s)", "pt": "%v / %m etapa(s)",
        "de": "%v / %m Schritt(e)",
    },
    "err_no_outlet": {
        "fr": "✘ Définissez d'abord un exutoire sur la carte.",
        "en": "✘ Please pick an outlet on the map first.",
        "es": "✘ Defina primero un punto de salida en el mapa.",
        "pt": "✘ Defina primeiro um exutório no mapa.",
        "de": "✘ Bitte zuerst einen Auslass auf der Karte wählen.",
    },
    "step_running": {
        "fr": "Étape {step}/{total} : {label}",
        "en": "Step {step}/{total}: {label}",
        "es": "Etapa {step}/{total}: {label}",
        "pt": "Etapa {step}/{total}: {label}",
        "de": "Schritt {step}/{total}: {label}",
    },
    "done_ok": {
        "fr": "✔ Bassin versant délimité en {seconds:.0f} s.",
        "en": "✔ Watershed delineated in {seconds:.0f} s.",
        "es": "✔ Cuenca delimitada en {seconds:.0f} s.",
        "pt": "✔ Bacia delimitada em {seconds:.0f} s.",
        "de": "✔ Einzugsgebiet in {seconds:.0f} s abgegrenzt.",
    },
    "done_error": {
        "fr": "✘ Échec : {error}",
        "en": "✘ Failed: {error}",
        "es": "✘ Fallo: {error}",
        "pt": "✘ Falha: {error}",
        "de": "✘ Fehlgeschlagen: {error}",
    },
    "warning": {
        "fr": "⚠ {message}",
        "en": "⚠ {message}",
        "es": "⚠ {message}",
        "pt": "⚠ {message}",
        "de": "⚠ {message}",
    },

    # --- Bassin hors gabarit ----------------------------------------------
    "oversize_title": {
        "fr": "Bassin trop grand",
        "en": "Watershed too large",
        "es": "Cuenca demasiado grande",
        "pt": "Bacia demasiado grande",
        "de": "Einzugsgebiet zu groß",
    },
    "oversize_text": {
        "fr": "Ce bassin dépasse ce que le traitement charge et n'a pas été "
              "calcule.\n\nIl faudrait {count} tronçons de réseau, quand la "
              "limite est de {budget}. Le bassin rendu serait tronqué, sans "
              "que rien ne l'indique sur la carte.",
        "en": "This watershed exceeds what the run will load and was not "
              "computed.\n\nIt would take {count} network reaches against a "
              "limit of {budget}. The resulting basin would be clipped, with "
              "nothing on the map to show it.",
        "es": "Esta cuenca supera lo que el proceso carga y no se ha "
              "calculado.\n\nHarían falta {count} tramos de red, frente a un "
              "límite de {budget}. La cuenca resultante estaría truncada, sin "
              "ninguna señal en el mapa.",
        "pt": "Esta bacia excede o que o processamento carrega e não foi "
              "calculada.\n\nSeriam precisos {count} troços de rede, para um "
              "limite de {budget}. A bacia obtida ficaria truncada, sem "
              "qualquer indicação no mapa.",
        "de": "Dieses Einzugsgebiet übersteigt, was der Lauf lädt, und wurde "
              "nicht berechnet.\n\nNötig wären {count} Gewässerabschnitte bei "
              "einer Grenze von {budget}. Das Ergebnis wäre abgeschnitten, "
              "ohne Hinweis in der Karte.",
    },
    "oversize_detail": {
        "fr": "Zone hydrographique : {zone}\n"
              "Déjà parcouru : {upstream} tronçons, {lineaire_km:.0f} km de "
              "linéaire, jusqu'à l'échelle du {scale}.\n\n"
              "Placer l'exutoire plus en amont donne un bassin juste en "
              "quelques secondes. Aller jusqu'à {max_count} tronçons reste "
              "possible, mais le calcul se compte en minutes et la maille du "
              "MNT sera grossière.",
        "en": "Hydrographic zone: {zone}\n"
              "Already walked: {upstream} reaches, {lineaire_km:.0f} km of "
              "network, up to the {scale} level.\n\n"
              "Moving the outlet further upstream gives a correct basin in "
              "seconds. Going to {max_count} reaches is still possible, but "
              "expect minutes and a coarse DEM cell size.",
        "es": "Zona hidrográfica: {zone}\n"
              "Ya recorrido: {upstream} tramos, {lineaire_km:.0f} km de red, "
              "hasta la escala del {scale}.\n\n"
              "Situar el punto de salida más aguas arriba da una cuenca "
              "correcta en segundos. Llegar a {max_count} tramos es posible, "
              "pero el cálculo dura minutos y la malla del MDT será gruesa.",
        "pt": "Zona hidrográfica: {zone}\n"
              "Já percorrido: {upstream} troços, {lineaire_km:.0f} km de "
              "rede, até a escala do {scale}.\n\n"
              "Colocar o exutório mais a montante da uma bacia correta em "
              "segundos. Chegar a {max_count} troços e possível, mas o "
              "cálculo demora minutos e a malha do MDT será grosseira.",
        "de": "Hydrografische Zone: {zone}\n"
              "Bereits durchlaufen: {upstream} Abschnitte, "
              "{lineaire_km:.0f} km Netz, bis zur Ebene {scale}.\n\n"
              "Ein Auslass weiter oberhalb liefert in Sekunden ein korrektes "
              "Gebiet. Bis {max_count} Abschnitte ist es möglich, dauert aber "
              "Minuten bei gröber Rasterweite.",
    },
    "oversize_zone_unknown": {
        "fr": "non identifiée", "en": "not identified",
        "es": "no identificada", "pt": "não identificada",
        "de": "nicht ermittelt",
    },
    "oversize_go": {
        "fr": "Calculer quand même (long)",
        "en": "Compute anyway (slow)",
        "es": "Calcular de todos modos (lento)",
        "pt": "Calcular mesmo assim (lento)",
        "de": "Trotzdem berechnen (langsam)",
    },
    "oversize_back": {
        "fr": "Choisir un autre exutoire",
        "en": "Pick another outlet",
        "es": "Elegir otro punto de salida",
        "pt": "Escolher outro exutório",
        "de": "Anderen Auslass wählen",
    },
    "oversize_status": {
        "fr": "✘ Bassin trop grand : calcul non lance.",
        "en": "✘ Watershed too large: not computed.",
        "es": "✘ Cuenca demasiado grande: no calculada.",
        "pt": "✘ Bacia demasiado grande: não calculada.",
        "de": "✘ Einzugsgebiet zu groß: nicht berechnet.",
    },
    "oversize_log": {
        "fr": "\u26a0 Limite atteinte : {count} tronçons seraient à charger, "
              "pour un maximum de {budget}. {upstream} tronçons amont déjà "
              "parcourus, {lineaire_km:.0f} km de linéaire.",
        "en": "\u26a0 Limit reached: {count} reaches would have to be "
              "loaded, against a maximum of {budget}. {upstream} upstream "
              "reaches already walked, {lineaire_km:.0f} km of network.",
        "es": "\u26a0 Límite alcanzado: habría que cargar {count} tramos, "
              "para un máximo de {budget}. {upstream} tramos aguas arriba ya "
              "recorridos, {lineaire_km:.0f} km de red.",
        "pt": "\u26a0 Limite atingido: seriam precisos {count} troços, para "
              "um máximo de {budget}. {upstream} troços a montante já "
              "percorridos, {lineaire_km:.0f} km de rede.",
        "de": "\u26a0 Grenze erreicht: {count} Abschnitte wären zu laden, "
              "bei maximal {budget}. {upstream} Abschnitte oberhalb bereits "
              "durchlaufen, {lineaire_km:.0f} km Netz.",
    },
    "resuming": {
        "fr": "\u21bb Reprise du calcul : {dalles} dalles et {troncons} "
              "tronçons déjà en mémoire, on repart de la.",
        "en": "\u21bb Resuming: {dalles} tiles and {troncons} reaches already "
              "in memory, carrying on from there.",
        "es": "\u21bb Reanudación: {dalles} teselas y {troncons} tramos ya en "
              "memoria, se continúa desde ahí.",
        "pt": "\u21bb Retoma: {dalles} mosaicos e {troncons} troços já em "
              "memória, continua-se daí.",
        "de": "\u21bb Fortsetzung: {dalles} Kacheln und {troncons} Abschnitte "
              "bereits im Speicher, es geht dort weiter.",
    },
    "oversize_accepted": {
        "fr": "Calcul intégral demandé : le budget de tronçons est relevé, "
              "le calcul se poursuit.",
        "en": "Full computation requested: the reach budget is raised, the "
              "run carries on.",
        "es": "Cálculo integral solicitado: se eleva el límite de tramos, el "
              "cálculo continúa.",
        "pt": "Cálculo integral pedido: o limite de troços e elevado, o "
              "cálculo prossegue.",
        "de": "Vollständige Berechnung angefordert: die Abschnittsgrenze wird "
              "angehoben, der Lauf geht weiter.",
    },

    # --- A propos ---------------------------------------------------------
    "about_title": {
        "fr": "À propos de BVLIP", "en": "About BVLIP",
        "es": "Acerca de BVLIP", "pt": "Acerca do BVLIP",
        "de": "Über BVLIP",
    },
    "version_label": {
        "fr": "Version {version}", "en": "Version {version}",
        "es": "Versión {version}", "pt": "Versão {version}",
        "de": "Version {version}",
    },
    "report_bug": {
        "fr": "Signaler un bug", "en": "Report a bug",
        "es": "Informar de un error", "pt": "Reportar um erro",
        "de": "Fehler melden",
    },
    "close": {
        "fr": "Fermer", "en": "Close", "es": "Cerrar",
        "pt": "Fechar", "de": "Schließen",
    },
    "about_limits": {
        "fr": "Taille du bassin : la délimitation charge jusqu'à {guard} "
              "tronçons de réseau, et jusqu'à {hard} si vous le demandez "
              "explicitement. Ces deux plafonds sont ceux que le plugin se "
              "fixe pour tenir en mémoire, non des limites de la "
              "Géoplateforme. Au-delà, BVLIP refuse plutôt que de rendre un "
              "bassin coupe au bord de l'emprise.",
        "en": "Catchment size: delineation loads up to {guard} network "
              "reaches, and up to {hard} if you explicitly ask. Both "
              "ceilings are the plugin's own, set to stay within memory, not "
              "Geoplateforme limits. Beyond them BVLIP refuses rather than "
              "return a basin clipped at the extent border.",
        "es": "Tamaño de la cuenca: la delimitación carga hasta {guard} "
              "tramos de red, y hasta {hard} si lo pide expresamente. Ambos "
              "límites son los que el complemento se fija para caber en "
              "memoria, no límites de la Géoplateforme. Más allá, BVLIP "
              "rechaza en lugar de devolver una cuenca cortada.",
        "pt": "Tamanho da bacia: a delimitação carrega até {guard} troços de "
              "rede, e até {hard} se o pedir explicitamente. Ambos os "
              "limites são os do próprio complemento, para caber em memória, "
              "e não limites da Géoplateforme. Para além disso, o BVLIP "
              "recusa em vez de devolver uma bacia cortada.",
        "de": "Gebietsgröße: die Abgrenzung lädt bis zu {guard} "
              "Gewässerabschnitte, auf ausdrücklichen Wunsch bis {hard}. "
              "Beide Grenzen setzt das Plugin selbst, um im Speicher zu "
              "bleiben; es sind keine Grenzen der Géoplateforme. Darüber "
              "lehnt BVLIP ab, statt ein am Rand abgeschnittenes Gebiet zu "
              "liefern.",
    },
    "data_credit": {
        "fr": "Données : RGE ALTI, BD TOPO, BD TOPAGE — IGN / Sandre",
        "en": "Data: RGE ALTI, BD TOPO, BD TOPAGE — IGN / Sandre",
        "es": "Datos: RGE ALTI, BD TOPO, BD TOPAGE — IGN / Sandre",
        "pt": "Dados: RGE ALTI, BD TOPO, BD TOPAGE — IGN / Sandre",
        "de": "Daten: RGE ALTI, BD TOPO, BD TOPAGE — IGN / Sandre",
    },
}


def tr(key, lang, **kwargs):
    """Traduit une cle dans la langue demandee.

    Repli sur l'anglais, puis sur la cle elle-meme. Une erreur de formatage
    ne doit jamais faire tomber l'interface : si un placeholder manque, la
    chaine brute est renvoyee telle quelle.
    """
    entry = TR.get(key)
    if entry is None:
        return key
    text = entry.get(lang) or entry.get(FALLBACK) or key
    if not kwargs:
        return text
    try:
        return text.format(**kwargs)
    except (KeyError, IndexError, ValueError):
        return text


def resolve_language(qgis_locale):
    """Retient le code langue a deux lettres s'il est gere, sinon l'anglais."""
    code = (qgis_locale or "")[:2].lower()
    return code if any(code == c for c, _ in LANGUAGES) else FALLBACK
