# -*- coding: utf-8 -*-
"""Traductions embarquees de BVLIP (FR / EN / ES / PT / DE).

Le plugin n'utilise pas les fichiers .qm de Qt : le dictionnaire ci-dessous
suffit pour un plugin de cette taille et evite une etape de compilation.
La langue par defaut suit celle de QGIS, et l'utilisateur peut la changer
a la volee depuis le panneau.
"""

LANGUAGES = [
    ("fr", "Francais"),
    ("en", "English"),
    ("es", "Espanol"),
    ("pt", "Portugues"),
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
        "de": "BVLIP-Bereich offnen",
    },
    "action_tooltip": {
        "fr": "Delimiter le bassin versant en amont d'un point",
        "en": "Delineate the watershed upstream of a point",
        "es": "Delimitar la cuenca aguas arriba de un punto",
        "pt": "Delimitar a bacia a montante de um ponto",
        "de": "Einzugsgebiet oberhalb eines Punktes abgrenzen",
    },
    "menu_settings": {
        "fr": "Réglages...", "en": "Settings...", "es": "Ajustes...",
        "pt": "Definicoes...", "de": "Einstellungen...",
    },
    "settings_title": {
        "fr": "BVLIP - Réglages",
        "en": "BVLIP - Settings",
        "es": "BVLIP - Ajustes",
        "pt": "BVLIP - Definicoes",
        "de": "BVLIP - Einstellungen",
    },
    "group_snapping": {
        "fr": "Accrochage de l'exutoire",
        "en": "Outlet snapping",
        "es": "Ajuste del punto de salida",
        "pt": "Ajuste do exutorio",
        "de": "Fang des Auslasses",
    },
    "about": {
        "fr": "A propos", "en": "About", "es": "Acerca de",
        "pt": "Acerca de", "de": "Uber",
    },
    "language": {
        "fr": "Langue", "en": "Language", "es": "Idioma",
        "pt": "Idioma", "de": "Sprache",
    },

    # --- Exutoire ---------------------------------------------------------
    "group_outlet": {
        "fr": "Exutoire", "en": "Outlet", "es": "Punto de salida",
        "pt": "Exutorio", "de": "Auslass",
    },
    "btn_pick": {
        "fr": "Cliquer un point sur la carte",
        "en": "Pick a point on the map",
        "es": "Seleccionar un punto en el mapa",
        "pt": "Selecionar um ponto no mapa",
        "de": "Punkt auf der Karte wahlen",
    },
    "no_outlet": {
        "fr": "Aucun exutoire defini",
        "en": "No outlet defined",
        "es": "Ningun punto de salida definido",
        "pt": "Nenhum exutorio definido",
        "de": "Kein Auslass definiert",
    },
    "outlet_set": {
        "fr": "Exutoire : {x:.1f} ; {y:.1f} (Lambert 93)",
        "en": "Outlet: {x:.1f} ; {y:.1f} (Lambert 93)",
        "es": "Punto de salida: {x:.1f} ; {y:.1f} (Lambert 93)",
        "pt": "Exutorio: {x:.1f} ; {y:.1f} (Lambert 93)",
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
        "fr": "Distance a laquelle chercher un chenal du modele de terrain "
              "autour de l'exutoire. Le trace cartographique d'un cours "
              "d'eau et le talweg calcule s'ecartent couramment de plusieurs "
              "dizaines de metres en fond de vallee.",
        "en": "How far to look for a channel of the terrain model around "
              "the outlet. A mapped watercourse and the computed thalweg "
              "commonly differ by tens of metres in valley bottoms.",
        "es": "Radio de busqueda de la celda mas drenada alrededor del punto "
              "de salida. 0 desactiva el reajuste.",
        "pt": "Raio de busca da celula mais drenada em torno do exutorio. "
              "0 desativa o reajuste.",
        "de": "Suchradius fur die am starksten entwasserte Zelle um den "
              "Auslass. 0 schaltet den Nachfang ab.",
    },
    "snap_radius": {
        "fr": "Rayon d'accrochage au reseau (m)",
        "en": "Snapping radius to the network (m)",
        "es": "Radio de ajuste a la red (m)",
        "pt": "Raio de ajuste a rede (m)",
        "de": "Fangradius zum Netz (m)",
    },

    # --- Options ----------------------------------------------------------
    "group_options": {
        "fr": "Donnees a rapatrier",
        "en": "Data to retrieve",
        "es": "Datos a recuperar",
        "pt": "Dados a obter",
        "de": "Abzurufende Daten",
    },
    "btn_select_all": {
        "fr": "Tout cocher", "en": "Select all", "es": "Marcar todo",
        "pt": "Marcar tudo", "de": "Alle wahlen",
    },
    "btn_select_none": {
        "fr": "Tout decocher", "en": "Clear all", "es": "Desmarcar todo",
        "pt": "Desmarcar tudo", "de": "Alle abwahlen",
    },
    "datasets_count": {
        "fr": "{0} / {1} donnees",
        "en": "{0} / {1} datasets",
        "es": "{0} / {1} datos",
        "pt": "{0} / {1} dados",
        "de": "{0} / {1} Datensatze",
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
        "pt": "Agricola", "de": "Landwirtschaft",
    },
    "dstab_zonages": {
        "fr": "Zonages", "en": "Designations", "es": "Zonificacion",
        "pt": "Zonamentos", "de": "Schutzgebiete",
    },
    "dstab_eau": {
        "fr": "Eau", "en": "Water", "es": "Agua",
        "pt": "Agua", "de": "Wasser",
    },

    # --- Donnees : onglet Bassin ------------------------------------------
    "ds_metriques": {
        "fr": "Metriques morphometriques",
        "en": "Morphometric metrics",
        "es": "Metricas morfometricas",
        "pt": "Metricas morfometricas",
        "de": "Morphometrische Kennwerte",
    },
    "ds_affinage": {
        "fr": "Recalculer a la maille la plus fine",
        "en": "Recompute at the finest cell size",
        "es": "Recalcular con la malla mas fina",
        "pt": "Recalcular com a malha mais fina",
        "de": "Mit der feinsten Zellgrosse neu berechnen",
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
        "fr": "Bati BD TOPO",
        "en": "BD TOPO buildings",
        "es": "Edificacion BD TOPO",
        "pt": "Edificado BD TOPO",
        "de": "Bebauung BD TOPO",
    },
    "ds_foret": {
        "fr": "Couvert forestier BD Foret v2",
        "en": "BD Foret v2 forest cover",
        "es": "Cubierta forestal BD Foret v2",
        "pt": "Coberto florestal BD Foret v2",
        "de": "Waldbedeckung BD Foret v2",
    },

    # --- Donnees : onglet Agricole ----------------------------------------
    "ds_rpg": {
        "fr": "Parcelles PAC (RPG)",
        "en": "CAP parcels (RPG)",
        "es": "Parcelas PAC (RPG)",
        "pt": "Parcelas PAC (RPG)",
        "de": "GAP-Schlage (RPG)",
    },
    "dsinfo_rpg": {
        "fr": "Registre parcellaire graphique : les parcelles declarees "
              "chaque annee par les exploitants au titre de la politique "
              "agricole commune. Surface declaree dans le bassin, part de "
              "celui-ci, nombre et taille des parcelles, repartition entre "
              "terres arables, cultures permanentes et prairies, et le detail "
              "des cultures. Attention : le RPG ne couvre que le declare - un "
              "exploitant qui ne demande pas d'aide n'y figure pas. La "
              "surface obtenue minore la surface agricole reelle.",
        "en": "Graphic parcel register: the plots declared each year by "
              "farmers under the common agricultural policy. Declared area "
              "within the basin, its share, parcel count and size, split "
              "between arable land, permanent crops and grassland, and the "
              "crop detail. Mind that the register covers only what is "
              "declared - a farmer claiming no aid does not appear - so the "
              "area is a lower bound of the real farmland.",
        "es": "Registro parcelario grafico : las parcelas declaradas cada "
              "ano por los agricultores en el marco de la PAC. Superficie "
              "declarada, numero y tamano de parcelas, reparto entre tierras "
              "arables, cultivos permanentes y pastos. Solo cubre lo "
              "declarado : es un minimo de la superficie agraria real.",
        "pt": "Registo parcelar grafico : as parcelas declaradas todos os "
              "anos pelos agricultores no ambito da PAC. Area declarada, "
              "numero e dimensao das parcelas, reparticao entre terras "
              "araveis, culturas permanentes e prados. So cobre o declarado : "
              "e um minimo da area agricola real.",
        "de": "Grafisches Schlagverzeichnis: die jahrlich von den Betrieben "
              "im Rahmen der GAP gemeldeten Schlage. Gemeldete Flache, Zahl "
              "und Grosse der Schlage, Aufteilung in Ackerland, Dauerkulturen "
              "und Grunland. Erfasst nur Gemeldetes und ist daher eine "
              "Untergrenze der tatsachlichen Agrarflache.",
    },
    "ds_bio": {
        "fr": "Agriculture biologique",
        "en": "Organic farming",
        "es": "Agricultura ecologica",
        "pt": "Agricultura biologica",
        "de": "Okologischer Landbau",
    },
    "dsinfo_bio": {
        "fr": "Parcelles declarees en agriculture biologique ou en cours de "
              "conversion, avec leur stade - certifiee, ou premiere, deuxieme "
              "ou troisieme annee de conversion. Surface, part du bassin et "
              "part de la surface declaree. Les engagements en mesures "
              "agroenvironnementales et climatiques, eux, ne sont pas publies "
              "a la parcelle : c'est une donnee d'aide individuelle, et le "
              "bio est ce qui s'en approche le plus dans l'ouvert.",
        "en": "Plots declared under organic farming or in conversion, with "
              "their stage - certified, or first, second or third year of "
              "conversion. Area, share of the basin and share of the declared "
              "area. Agri-environmental scheme commitments are not published "
              "at plot level - they are individual aid data - and organic "
              "farming is the closest open substitute.",
        "es": "Parcelas declaradas en agricultura ecologica o en conversion, "
              "con su fase. Superficie, parte de la cuenca y de la superficie "
              "declarada. Los compromisos agroambientales no se publican por "
              "parcela : el ecologico es lo mas cercano en datos abiertos.",
        "pt": "Parcelas declaradas em agricultura biologica ou em conversao, "
              "com a sua fase. Area, parte da bacia e da area declarada. Os "
              "compromissos agroambientais nao sao publicados a parcela : o "
              "biologico e o mais proximo nos dados abertos.",
        "de": "Als okologisch oder in Umstellung gemeldete Schlage, mit ihrer "
              "Stufe. Flache, Anteil am Gebiet und an der gemeldeten Flache. "
              "Agrarumweltverpflichtungen werden nicht schlagbezogen "
              "veroffentlicht; der Okolandbau kommt dem am nachsten.",
    },
    "ds_prairies": {
        "fr": "Prairies sensibles (BCAE)",
        "en": "Sensitive grassland (GAEC)",
        "es": "Pastos sensibles (BCAM)",
        "pt": "Prados sensiveis (BCAA)",
        "de": "Sensibles Dauergrunland (GLOZ)",
    },
    "dsinfo_prairies": {
        "fr": "Prairies et paturages permanents situes en zone Natura 2000 "
              "et proteges au titre des bonnes conditions agricoles et "
              "environnementales : leur retournement est interdit. Leur "
              "interet ici est autant hydrologique qu'agricole - une prairie "
              "permanente retient l'eau et le sol la ou un labour les laisse "
              "partir.",
        "en": "Permanent grassland and pasture inside Natura 2000 areas, "
              "protected under good agricultural and environmental "
              "conditions: ploughing them is forbidden. Their interest here "
              "is as much hydrological as agricultural - permanent grassland "
              "holds water and soil where tillage lets both go.",
        "es": "Pastos permanentes en zona Natura 2000, protegidos por las "
              "buenas condiciones agrarias y medioambientales : su laboreo "
              "esta prohibido. Interes tanto hidrologico como agrario.",
        "pt": "Prados permanentes em zona Natura 2000, protegidos pelas boas "
              "condicoes agricolas e ambientais : a lavoura e proibida. "
              "Interesse tanto hidrologico como agricola.",
        "de": "Dauergrunland in Natura-2000-Gebieten, nach den GLOZ-"
              "Standards geschutzt: Umbruch ist verboten. Ebenso "
              "hydrologisch wie landwirtschaftlich von Belang.",
    },
    "ds_aoc": {
        "fr": "Aires AOC viticoles",
        "en": "Wine PDO areas",
        "es": "Areas DOP vitivinicolas",
        "pt": "Areas DOP vitivinicolas",
        "de": "Weinbau-Ursprungsgebiete",
    },
    "dsinfo_aoc": {
        "fr": "Delimitation parcellaire des appellations d'origine "
              "controlee viticoles, etablie par l'INAO. Surface classee dans "
              "le bassin et part de celui-ci. Ne rend rien la ou il n'y a pas "
              "de vigne, ce qui est le cas de la plus grande partie du "
              "territoire.",
        "en": "Parcel-level delineation of wine protected designations of "
              "origin, set by the INAO. Classified area within the basin and "
              "its share. Returns nothing where there are no vines, which is "
              "most of the country.",
        "es": "Delimitacion parcelaria de las denominaciones de origen "
              "vitivinicolas, establecida por el INAO. Superficie clasificada "
              "en la cuenca. Vacia alli donde no hay vina.",
        "pt": "Delimitacao parcelar das denominacoes de origem vitivinicolas, "
              "estabelecida pelo INAO. Area classificada na bacia. Vazia onde "
              "nao ha vinha.",
        "de": "Parzellenscharfe Abgrenzung der Weinbau-Ursprungs"
              "bezeichnungen des INAO. Ausgewiesene Flache im Gebiet. Ohne "
              "Rebflachen bleibt sie leer.",
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
        "fr": "Arrete de protection de biotope",
        "en": "Biotope protection order",
        "es": "Orden de proteccion de biotopo",
        "pt": "Despacho de protecao de biotopo",
        "de": "Biotopschutzverordnung",
    },
    "ds_rnn": {
        "fr": "Reserve naturelle nationale",
        "en": "National nature reserve",
        "es": "Reserva natural nacional",
        "pt": "Reserva natural nacional",
        "de": "Nationales Naturschutzgebiet",
    },
    "ds_rnr": {
        "fr": "Reserve naturelle regionale",
        "en": "Regional nature reserve",
        "es": "Reserva natural regional",
        "pt": "Reserva natural regional",
        "de": "Regionales Naturschutzgebiet",
    },
    "ds_pnr": {
        "fr": "Parc naturel regional",
        "en": "Regional nature park",
        "es": "Parque natural regional",
        "pt": "Parque natural regional",
        "de": "Regionaler Naturpark",
    },
    "ds_ramsar": {
        "fr": "Site Ramsar",
        "en": "Ramsar site",
        "es": "Sitio Ramsar",
        "pt": "Sitio Ramsar",
        "de": "Ramsar-Gebiet",
    },
    "ds_zhumide": {
        "fr": "Zones humides et tourbieres",
        "en": "Wetlands and peatlands",
        "es": "Humedales y turberas",
        "pt": "Zonas humidas e turfeiras",
        "de": "Feuchtgebiete und Moore",
    },
    "ds_nitrate": {
        "fr": "Zone vulnerable aux nitrates",
        "en": "Nitrate vulnerable zone",
        "es": "Zona vulnerable a nitratos",
        "pt": "Zona vulneravel aos nitratos",
        "de": "Nitratgefahrdetes Gebiet",
    },
    "ds_eutroph": {
        "fr": "Zone sensible a l'eutrophisation",
        "en": "Area sensitive to eutrophication",
        "es": "Zona sensible a la eutrofizacion",
        "pt": "Zona sensivel a eutrofizacao",
        "de": "Eutrophierungsempfindliches Gebiet",
    },

    # --- Donnees : onglet Eau ---------------------------------------------
    "ds_masse_eau": {
        "fr": "Masse d'eau DCE de surface",
        "en": "WFD surface water body",
        "es": "Masa de agua superficial DMA",
        "pt": "Massa de agua superficial DQA",
        "de": "WRRL-Oberflachenwasserkorper",
    },
    "ds_meso": {
        "fr": "Masse d'eau souterraine",
        "en": "Groundwater body",
        "es": "Masa de agua subterranea",
        "pt": "Massa de agua subterranea",
        "de": "Grundwasserkorper",
    },
    "ds_her": {
        "fr": "Hydroecoregions 1 et 2",
        "en": "Hydro-ecoregions 1 and 2",
        "es": "Hidroecorregiones 1 y 2",
        "pt": "Hidroecorregioes 1 e 2",
        "de": "Hydrooekoregionen 1 und 2",
    },
    "ds_roe": {
        "fr": "Obstacles a l'ecoulement (ROE)",
        "en": "Barriers to flow (ROE)",
        "es": "Obstaculos al flujo (ROE)",
        "pt": "Obstaculos ao escoamento (ROE)",
        "de": "Querbauwerke (ROE)",
    },
    "ds_hydrometrie": {
        "fr": "Sites hydrometriques",
        "en": "Gauging sites",
        "es": "Estaciones de aforo",
        "pt": "Estacoes hidrometricas",
        "de": "Pegelstationen",
    },

    # --- Descriptions longues, au survol du i ------------------------------
    "dsinfo_metriques": {
        "fr": "Surface, perimetre, indice de compacite de Gravelius, "
              "rectangle equivalent, hypsometrie en neuf points, pentes "
              "moyenne et mediane, indice de pente global, denivelee "
              "specifique, plus long cheminement hydraulique et densite de "
              "drainage. Tout se calcule sur le modele de terrain deja "
              "telecharge : aucune requete de plus.",
        "en": "Area, perimeter, Gravelius compactness index, equivalent "
              "rectangle, nine-point hypsometry, mean and median slopes, "
              "global slope index, specific relief, longest flow path and "
              "drainage density. All computed on the elevation model already "
              "downloaded: no further request.",
        "es": "Superficie, perimetro, indice de Gravelius, rectangulo "
              "equivalente, hipsometria, pendientes, indice de pendiente "
              "global, desnivel especifico, cauce mas largo y densidad de "
              "drenaje. Se calcula sobre el MDT ya descargado.",
        "pt": "Area, perimetro, indice de Gravelius, retangulo equivalente, "
              "hipsometria, declives, indice de declive global, desnivel "
              "especifico, percurso mais longo e densidade de drenagem. "
              "Calculado sobre o MDT ja descarregado.",
        "de": "Flache, Umfang, Gravelius-Index, Aquivalentrechteck, "
              "Hypsometrie, Hangneigungen, globaler Neigungsindex, "
              "spezifisches Relief, langster Fliessweg und Entwasserungs"
              "dichte. Alles aus dem bereits geladenen Hohenmodell.",
    },
    "dsinfo_affinage": {
        "fr": "Sur un grand bassin, la maille du modele de terrain est "
              "elargie faute de memoire. Cette option relance un second "
              "calcul sur le bassin recadre, ce qui permet de revenir a 5 m. "
              "Environ deux fois plus long, et sans effet sur la surface : "
              "n'a d'interet que si la pente ou le plus long cheminement "
              "comptent.",
        "en": "On a large catchment the cell size is enlarged for lack of "
              "memory. This option runs a second pass on the cropped basin, "
              "back down to 5 m. About twice as long, and it does not change "
              "the area: worth it only when slope or the longest flow path "
              "matter.",
        "es": "En una cuenca grande la malla se amplia por falta de memoria. "
              "Esta opcion relanza un segundo calculo sobre la cuenca "
              "recortada, hasta 5 m. Dura el doble y no cambia la superficie.",
        "pt": "Numa bacia grande a malha e alargada por falta de memoria. "
              "Esta opcao repete o calculo sobre a bacia recortada, ate 5 m. "
              "Demora o dobro e nao altera a area.",
        "de": "Bei grossen Gebieten wird die Zellgrosse aus Speichermangel "
              "vergrossert. Diese Option rechnet ein zweites Mal auf dem "
              "zugeschnittenen Gebiet, zuruck auf 5 m. Etwa doppelt so "
              "lange, ohne die Flache zu andern.",
    },

    "dsinfo_corine": {
        "fr": "Repartition de l'occupation du sol en quarante-quatre classes "
              "et cinq grands postes, avec la classe dominante et sa part. "
              "Millesime 2018. Unite minimale de collecte de 25 ha : les "
              "hameaux et les petits boisements n'y figurent pas, d'ou le "
              "bati de la BD TOPO et la BD Foret a cote.",
        "en": "Land cover split into forty-four classes and five broad "
              "groups, with the dominant class and its share. 2018 vintage. "
              "25 ha minimum mapping unit: hamlets and small woods are "
              "absent, hence BD TOPO buildings and BD Foret alongside.",
        "es": "Ocupacion del suelo en cuarenta y cuatro clases y cinco "
              "grupos, con la clase dominante. Edicion 2018, unidad minima "
              "de 25 ha : las aldeas y los bosquetes no aparecen.",
        "pt": "Ocupacao do solo em quarenta e quatro classes e cinco grupos, "
              "com a classe dominante. Edicao 2018, unidade minima de 25 ha : "
              "lugarejos e pequenos bosques nao constam.",
        "de": "Landbedeckung in vierundvierzig Klassen und funf Gruppen, mit "
              "der vorherrschenden Klasse. Stand 2018, Mindestkartierflache "
              "25 ha: Weiler und kleine Walder fehlen.",
    },
    "dsinfo_bati": {
        "fr": "Emprise au sol des batiments et surface des zones "
              "d'habitation, au metre pres, avec le nombre de batiments. "
              "Mesure independamment de Corine et jamais additionne a lui, "
              "ce qui compterait deux fois les memes surfaces. C'est l'etape "
              "la plus lourde sur un grand bassin : des dizaines de milliers "
              "de polygones.",
        "en": "Building footprints and settlement areas to the metre, with "
              "the building count. Measured independently of Corine and "
              "never added to it, which would count the same surfaces twice. "
              "The heaviest step on a large basin: tens of thousands of "
              "polygons.",
        "es": "Superficie construida y zonas de habitacion al metro, con el "
              "numero de edificios. Se mide aparte de Corine y nunca se suma "
              "a el. Es el paso mas pesado en una cuenca grande.",
        "pt": "Area de implantacao dos edificios e zonas de habitacao ao "
              "metro, com o numero de edificios. Medido a parte do Corine e "
              "nunca somado a ele. E a etapa mais pesada numa bacia grande.",
        "de": "Gebaudegrundflachen und Siedlungsflachen metergenau, mit "
              "Gebaudezahl. Unabhangig von Corine erhoben und nie dazu "
              "addiert. Der aufwandigste Schritt bei grossen Gebieten.",
    },
    "dsinfo_foret": {
        "fr": "Couvert forestier par formation vegetale, a 0,5 ha d'unite "
              "minimale, avec la part des feuillus, des coniferes et des "
              "peuplements mixtes. Deux totaux distincts : le couvert, qui "
              "comprend landes et formations herbacees, et la surface boisee, "
              "qui ne retient que les peuplements.",
        "en": "Forest cover by vegetation formation, 0.5 ha minimum unit, "
              "with the share of broadleaved, coniferous and mixed stands. "
              "Two distinct totals: cover, which includes heaths and "
              "herbaceous formations, and wooded area, which keeps stands "
              "only.",
        "es": "Cubierta forestal por formacion vegetal, unidad minima de "
              "0,5 ha, con la parte de frondosas, coniferas y mixtas. Dos "
              "totales : la cubierta, que incluye landas, y la superficie "
              "arbolada, solo las masas.",
        "pt": "Coberto florestal por formacao vegetal, unidade minima de "
              "0,5 ha, com a parte de folhosas, resinosas e mistas. Dois "
              "totais : o coberto, que inclui landes, e a area arborizada, "
              "apenas os povoamentos.",
        "de": "Waldbedeckung nach Vegetationsformation, Mindestflache "
              "0,5 ha, mit Anteil von Laub-, Nadel- und Mischbestanden. Zwei "
              "Summen: Bedeckung inklusive Heiden, und reine Waldflache.",
    },

    "dsinfo_znieff1": {
        "fr": "Zone naturelle d'interet ecologique, faunistique et "
              "floristique de type I : secteur de superficie limitee abritant "
              "des especes ou des milieux rares. C'est un inventaire "
              "scientifique et non une protection : elle n'interdit rien, "
              "mais un amenagement devra justifier de l'ignorer. Surface dans "
              "le bassin, part de celui-ci, et le nom des sites.",
        "en": "Type I ZNIEFF: a limited area holding rare species or "
              "habitats. A scientific inventory, not a protection: it forbids "
              "nothing, but a development will have to justify ignoring it. "
              "Area within the basin, its share, and the site names.",
        "es": "ZNIEFF de tipo I : sector de superficie limitada con especies "
              "o medios raros. Es un inventario cientifico, no una "
              "proteccion. Superficie en la cuenca, parte y nombre de los "
              "sitios.",
        "pt": "ZNIEFF de tipo I : setor de superficie limitada com especies "
              "ou meios raros. E um inventario cientifico, nao uma protecao. "
              "Area na bacia, parte e nome dos sitios.",
        "de": "ZNIEFF Typ I: kleinraumiges Gebiet mit seltenen Arten oder "
              "Lebensraumen. Ein wissenschaftliches Inventar, kein Schutz. "
              "Flache im Gebiet, Anteil und Namen der Standorte.",
    },
    "dsinfo_znieff2": {
        "fr": "ZNIEFF de type II : grand ensemble naturel riche et peu "
              "modifie, qui englobe le plus souvent plusieurs zones de type "
              "I. Les deux se superposent donc, et leurs surfaces ne "
              "s'additionnent pas. Inventaire scientifique, sans portee "
              "reglementaire.",
        "en": "Type II ZNIEFF: a large, rich and little-altered natural unit, "
              "usually enclosing several type I zones. The two therefore "
              "overlap and their areas do not add up. A scientific inventory, "
              "with no regulatory force.",
        "es": "ZNIEFF de tipo II : gran conjunto natural rico y poco "
              "modificado, que suele englobar varias zonas de tipo I. Ambas "
              "se superponen y sus superficies no se suman.",
        "pt": "ZNIEFF de tipo II : grande conjunto natural rico e pouco "
              "alterado, que engloba varias zonas de tipo I. As duas "
              "sobrepoem-se e as areas nao se somam.",
        "de": "ZNIEFF Typ II: grossraumige, reiche und wenig veranderte "
              "Naturraume, die meist mehrere Typ-I-Zonen umfassen. Beide "
              "uberlagern sich, ihre Flachen addieren sich nicht.",
    },
    "dsinfo_zsc": {
        "fr": "Zone speciale de conservation du reseau Natura 2000, designee "
              "au titre de la directive Habitats pour des milieux naturels ou "
              "des especes d'interet communautaire. Protection reglementaire "
              "reelle : tout projet susceptible d'affecter le site releve de "
              "l'evaluation des incidences. Recouvre souvent une ZPS.",
        "en": "Natura 2000 Special Area of Conservation, designated under "
              "the Habitats Directive. A real regulatory protection: any "
              "project liable to affect the site falls under appropriate "
              "assessment. Often overlaps an SPA.",
        "es": "Zona especial de conservacion de Natura 2000, designada por la "
              "directiva Habitats. Proteccion reglamentaria real : todo "
              "proyecto que pueda afectarla exige evaluacion de impacto.",
        "pt": "Zona especial de conservacao da rede Natura 2000, designada ao "
              "abrigo da diretiva Habitats. Protecao regulamentar real : "
              "qualquer projeto que a possa afetar exige avaliacao.",
        "de": "Natura-2000-Gebiet nach der FFH-Richtlinie. Echter "
              "rechtlicher Schutz: jedes Vorhaben, das das Gebiet "
              "beeintrachtigen kann, unterliegt der Vertraglichkeitsprufung.",
    },
    "dsinfo_zps": {
        "fr": "Zone de protection speciale du reseau Natura 2000, designee au "
              "titre de la directive Oiseaux. Meme portee reglementaire que "
              "la ZSC, mais un objet different : les oiseaux sauvages et "
              "leurs habitats. Les deux se superposent frequemment sur les "
              "memes vallees.",
        "en": "Natura 2000 Special Protection Area, designated under the "
              "Birds Directive. Same regulatory force as an SAC, different "
              "subject: wild birds and their habitats. The two frequently "
              "overlap on the same valleys.",
        "es": "Zona de especial proteccion para las aves de Natura 2000, "
              "directiva Aves. Misma fuerza reglamentaria que la ZEC, objeto "
              "distinto. Ambas se superponen a menudo.",
        "pt": "Zona de protecao especial da rede Natura 2000, diretiva Aves. "
              "Mesma forca regulamentar que a ZEC, objeto diferente. As duas "
              "sobrepoem-se frequentemente.",
        "de": "Natura-2000-Vogelschutzgebiet nach der Vogelschutzrichtlinie. "
              "Gleiche Rechtswirkung wie ein FFH-Gebiet, anderer Gegenstand. "
              "Beide uberlagern sich haufig.",
    },
    "dsinfo_apb": {
        "fr": "Arrete prefectoral de protection de biotope : interdiction "
              "d'activites pouvant nuire a un milieu qui abrite une espece "
              "protegee. Petites surfaces, souvent une portion de cours d'eau "
              "ou une tourbiere, mais la protection y est stricte et "
              "opposable.",
        "en": "Prefectural biotope protection order: activities liable to "
              "harm a habitat sheltering a protected species are forbidden. "
              "Small areas, often a river reach or a peat bog, but the "
              "protection is strict and enforceable.",
        "es": "Orden prefectoral de proteccion de biotopo : prohibe las "
              "actividades que puedan danar un medio con especies "
              "protegidas. Superficies pequenas, proteccion estricta.",
        "pt": "Despacho de protecao de biotopo : proibe atividades que possam "
              "prejudicar um meio com especies protegidas. Areas pequenas, "
              "protecao estrita.",
        "de": "Biotopschutzverordnung: verbietet Tatigkeiten, die einen "
              "Lebensraum geschutzter Arten schadigen konnen. Kleine "
              "Flachen, strenger und durchsetzbarer Schutz.",
    },
    "dsinfo_rnn": {
        "fr": "Reserve naturelle nationale : le niveau de protection le plus "
              "eleve apres le coeur de parc national. Creee par decret, dotee "
              "d'un plan de gestion et d'un gestionnaire. Rare : beaucoup de "
              "bassins n'en comptent aucune, et la ligne reste alors vide.",
        "en": "National nature reserve: the highest level of protection "
              "after a national park core. Created by decree, with a "
              "management plan and a manager. Rare: many basins hold none, "
              "and the row then stays empty.",
        "es": "Reserva natural nacional : el nivel de proteccion mas alto "
              "tras el nucleo de parque nacional. Rara : muchas cuencas no "
              "tienen ninguna.",
        "pt": "Reserva natural nacional : o nivel de protecao mais elevado "
              "apos o nucleo de parque nacional. Rara : muitas bacias nao "
              "tem nenhuma.",
        "de": "Nationales Naturschutzgebiet: hochste Schutzstufe nach der "
              "Kernzone eines Nationalparks. Selten: viele Gebiete haben "
              "keines.",
    },
    "dsinfo_rnr": {
        "fr": "Reserve naturelle regionale, creee par le conseil regional. "
              "Meme logique qu'une reserve nationale, a l'echelle de la "
              "region et souvent sur des surfaces plus modestes.",
        "en": "Regional nature reserve, created by the regional council. "
              "Same logic as a national reserve, at regional scale and often "
              "on smaller areas.",
        "es": "Reserva natural regional, creada por el consejo regional. "
              "Misma logica que la nacional, a escala regional.",
        "pt": "Reserva natural regional, criada pelo conselho regional. "
              "Mesma logica que a nacional, a escala regional.",
        "de": "Regionales Naturschutzgebiet, vom Regionalrat ausgewiesen. "
              "Gleiche Logik wie national, auf regionaler Ebene.",
    },
    "dsinfo_pnr": {
        "fr": "Parc naturel regional : territoire habite, classe pour la "
              "qualite de son patrimoine et gere par une charte. Ce n'est pas "
              "une protection reglementaire mais un projet de territoire, et "
              "les surfaces sont vastes - un parc couvre souvent tout un "
              "bassin versant.",
        "en": "Regional nature park: an inhabited territory classified for "
              "the quality of its heritage and run under a charter. Not a "
              "regulatory protection but a territorial project, and the areas "
              "are vast - a park often covers a whole catchment.",
        "es": "Parque natural regional : territorio habitado, clasificado por "
              "la calidad de su patrimonio y gestionado por una carta. No es "
              "una proteccion reglamentaria. Superficies muy amplias.",
        "pt": "Parque natural regional : territorio habitado, classificado "
              "pela qualidade do seu patrimonio e gerido por uma carta. Nao e "
              "uma protecao regulamentar. Areas muito vastas.",
        "de": "Regionaler Naturpark: besiedeltes Gebiet, wegen seines Erbes "
              "ausgewiesen und uber eine Charta gefuhrt. Kein rechtlicher "
              "Schutz, sondern ein Gebietsprojekt. Sehr grosse Flachen.",
    },
    "dsinfo_ramsar": {
        "fr": "Zone humide d'importance internationale au titre de la "
              "convention de Ramsar. Engagement de l'Etat plutot que "
              "protection opposable, mais le classement signale une zone "
              "humide majeure, ce qui compte directement pour un bassin "
              "versant.",
        "en": "Wetland of international importance under the Ramsar "
              "convention. A state commitment rather than an enforceable "
              "protection, but the listing flags a major wetland, which "
              "matters directly for a catchment.",
        "es": "Humedal de importancia internacional (convenio de Ramsar). "
              "Compromiso del Estado mas que proteccion oponible, pero senala "
              "un humedal importante.",
        "pt": "Zona humida de importancia internacional (convencao de "
              "Ramsar). Compromisso do Estado mais do que protecao oponivel, "
              "mas assinala uma zona humida importante.",
        "de": "Feuchtgebiet von internationaler Bedeutung (Ramsar-"
              "Konvention). Eher Staatsverpflichtung als durchsetzbarer "
              "Schutz, weist aber auf ein bedeutendes Feuchtgebiet hin.",
    },
    "dsinfo_zhumide": {
        "fr": "Zones humides et tourbieres protegees au titre de la bonne "
              "condition agricole et environnementale n°2 de la politique "
              "agricole commune. Leur interet ici est hydrologique autant "
              "qu'ecologique : ce sont les surfaces qui stockent et "
              "restituent l'eau.",
        "en": "Wetlands and peatlands protected under good agricultural and "
              "environmental condition 2 of the common agricultural policy. "
              "Their interest here is hydrological as much as ecological: "
              "these are the surfaces that store and release water.",
        "es": "Humedales y turberas protegidos por la condicion agraria y "
              "medioambiental n°2 de la PAC. Su interes es hidrologico tanto "
              "como ecologico : almacenan y restituyen el agua.",
        "pt": "Zonas humidas e turfeiras protegidas pela condicao agricola e "
              "ambiental n.2 da PAC. O interesse e hidrologico tanto quanto "
              "ecologico : armazenam e restituem a agua.",
        "de": "Feuchtgebiete und Moore nach GLOZ-Standard 2 der Gemeinsamen "
              "Agrarpolitik. Hier ebenso hydrologisch wie okologisch "
              "relevant: sie speichern und geben Wasser ab.",
    },
    "dsinfo_nitrate": {
        "fr": "Zone vulnerable aux nitrates d'origine agricole, delimitee au "
              "titre de la directive Nitrates. Ce zonage ne dit pas ce que le "
              "bassin a de remarquable mais ce qu'il subit : programme "
              "d'actions obligatoire pour les exploitations qui s'y trouvent.",
        "en": "Nitrate vulnerable zone under the Nitrates Directive. This "
              "designation says not what is remarkable about the basin but "
              "what it undergoes: a mandatory action programme applies to "
              "farms within it.",
        "es": "Zona vulnerable a los nitratos de origen agrario (directiva "
              "Nitratos). No dice lo que la cuenca tiene de notable sino lo "
              "que sufre : programa de actuacion obligatorio.",
        "pt": "Zona vulneravel aos nitratos de origem agricola (diretiva "
              "Nitratos). Nao diz o que a bacia tem de notavel mas o que "
              "sofre : programa de acao obrigatorio.",
        "de": "Nitratgefahrdetes Gebiet nach der Nitratrichtlinie. Sagt "
              "nicht, was am Gebiet bemerkenswert ist, sondern was es "
              "erleidet: verpflichtendes Aktionsprogramm fur Betriebe.",
    },
    "dsinfo_eutroph": {
        "fr": "Zone sensible a l'eutrophisation au titre de la directive eaux "
              "residuaires urbaines : le milieu y recoit des rejets qu'il ne "
              "dilue pas assez, ce qui impose un traitement pousse de l'azote "
              "ou du phosphore aux stations d'epuration. Vaste : de grands "
              "bassins entiers sont classes.",
        "en": "Area sensitive to eutrophication under the urban waste water "
              "directive: the receiving water does not dilute discharges "
              "enough, requiring advanced nitrogen or phosphorus treatment at "
              "treatment plants. Vast: entire large basins are designated.",
        "es": "Zona sensible a la eutrofizacion (directiva de aguas "
              "residuales urbanas) : exige tratamiento avanzado de nitrogeno "
              "o fosforo. Muy extensa : cuencas enteras estan clasificadas.",
        "pt": "Zona sensivel a eutrofizacao (diretiva das aguas residuais "
              "urbanas) : exige tratamento avancado de azoto ou fosforo. "
              "Muito vasta : bacias inteiras estao classificadas.",
        "de": "Eutrophierungsempfindliches Gebiet nach der "
              "Kommunalabwasserrichtlinie: erfordert weitergehende "
              "Stickstoff- oder Phosphorbehandlung. Sehr grossflachig.",
    },

    "dsinfo_masse_eau": {
        "fr": "Masse d'eau de surface au sens de la directive cadre sur "
              "l'eau : code europeen, denomination, surface de son bassin "
              "versant specifique et categorie. Le rattachement se fait par "
              "l'exutoire et non par le bassin ; si le point tombe hors de "
              "tout polygone, la masse d'eau la plus proche a 250 m est "
              "retenue et le rapport le signale.",
        "en": "Surface water body under the Water Framework Directive: "
              "European code, name, area of its specific catchment and "
              "category. Attached through the outlet, not the basin; if the "
              "point falls outside every polygon, the nearest water body "
              "within 250 m is used and the report says so.",
        "es": "Masa de agua superficial (DMA) : codigo europeo, "
              "denominacion, superficie de su cuenca y categoria. Se asigna "
              "por el punto de salida, no por la cuenca.",
        "pt": "Massa de agua superficial (DQA) : codigo europeu, "
              "denominacao, area da sua bacia e categoria. A ligacao faz-se "
              "pelo exutorio, nao pela bacia.",
        "de": "Oberflachenwasserkorper nach WRRL: EU-Code, Bezeichnung, "
              "Flache seines Teileinzugsgebiets und Kategorie. Zuordnung "
              "uber den Auslass, nicht uber das Gebiet.",
    },
    "dsinfo_meso": {
        "fr": "Masse d'eau souterraine sous l'exutoire : code, denomination, "
              "nature de l'ecoulement, caractere karstique et surface "
              "d'affleurement. Les nappes se superposent ; c'est celle qui "
              "affleure qui est retenue, parce que c'est elle qui echange "
              "avec le cours d'eau. Un bassin topographique ne coincide pas "
              "avec son bassin hydrogeologique.",
        "en": "Groundwater body under the outlet: code, name, flow type, "
              "karstic character and outcrop area. Aquifers overlap; the "
              "outcropping one is kept, being the one that exchanges with the "
              "stream. A topographic basin does not coincide with its "
              "hydrogeological one.",
        "es": "Masa de agua subterranea bajo el punto de salida : codigo, "
              "denominacion, naturaleza del flujo, caracter karstico y "
              "superficie aflorante. Se retiene la que aflora.",
        "pt": "Massa de agua subterranea sob o exutorio : codigo, "
              "denominacao, natureza do escoamento, carater carsico e area "
              "aflorante. Retem-se a que aflora.",
        "de": "Grundwasserkorper unter dem Auslass: Code, Bezeichnung, "
              "Fliessart, Verkarstung und Ausstrichflache. Genommen wird der "
              "ausstreichende Korper.",
    },
    "dsinfo_her": {
        "fr": "Hydroecoregions de niveau 1 et 2 : le decoupage qui sert de "
              "cadre de comparaison a la directive cadre sur l'eau. Les "
              "valeurs de reference d'un cours d'eau y sont etablies, et deux "
              "bassins d'hydroecoregions differentes ne se comparent pas. "
              "Deux lectures ponctuelles, quasiment gratuites.",
        "en": "Hydro-ecoregions levels 1 and 2: the framework the Water "
              "Framework Directive compares against. Reference values for a "
              "watercourse are set within them, and two basins from different "
              "hydro-ecoregions do not compare. Two point lookups, almost "
              "free.",
        "es": "Hidroecorregiones de nivel 1 y 2 : el marco de comparacion de "
              "la DMA. Dos cuencas de hidroecorregiones distintas no se "
              "comparan. Coste de calculo casi nulo.",
        "pt": "Hidroecorregioes de nivel 1 e 2 : o quadro de comparacao da "
              "DQA. Duas bacias de hidroecorregioes diferentes nao se "
              "comparam. Custo de calculo quase nulo.",
        "de": "Hydrookoregionen der Ebenen 1 und 2: der Vergleichsrahmen der "
              "WRRL. Zwei Gebiete aus verschiedenen Hydrookoregionen sind "
              "nicht vergleichbar. Nahezu kostenlos.",
    },
    "dsinfo_roe": {
        "fr": "Referentiel des obstacles a l'ecoulement : barrages, seuils, "
              "digues recenses dans le bassin, avec leur nombre, ceux encore "
              "existants, ceux classes Grenelle, ceux equipes d'une passe a "
              "poissons, la hauteur de chute cumulee et la densite au "
              "kilometre. La hauteur est reconstituee : le referentiel ne "
              "donne souvent qu'une classe, dont le milieu est retenu, et la "
              "somme est donc un minorant.",
        "en": "Register of barriers to flow: dams, weirs and dykes recorded "
              "in the basin, with their count, those still standing, those "
              "listed under the Grenelle, those with a fish pass, the "
              "cumulated head and the density per kilometre. Head is "
              "reconstructed: the register often gives only a class, whose "
              "midpoint is used, so the sum is a lower bound.",
        "es": "Registro de obstaculos al flujo : presas, azudes y diques de "
              "la cuenca, con su numero, los que tienen escala de peces, la "
              "altura de caida acumulada y la densidad por kilometro. La "
              "altura se reconstruye a partir de clases : es un minimo.",
        "pt": "Registo de obstaculos ao escoamento : barragens, acudes e "
              "diques da bacia, com o numero, os que tem passagem para "
              "peixes, a altura de queda acumulada e a densidade por "
              "quilometro. A altura e reconstituida : e um minimo.",
        "de": "Querbauwerksverzeichnis: Wehre, Damme und Sperren im Gebiet, "
              "mit Anzahl, Fischaufstiegen, kumulierter Fallhohe und Dichte "
              "je Kilometer. Die Fallhohe wird aus Klassen rekonstruiert und "
              "ist daher eine Untergrenze.",
    },
    "dsinfo_hydrometrie": {
        "fr": "Sites hydrometriques du Sandre situes dans le bassin, avec "
              "leur code et leur gestionnaire. La question a laquelle ils "
              "repondent est simple et se pose toujours : le bassin est-il "
              "jauge, ou faudra-t-il reconstituer ses debits ? Un zero est "
              "une reponse, pas une absence de donnee.",
        "en": "Sandre gauging sites inside the basin, with their code and "
              "operator. The question they answer is simple and always "
              "arises: is the basin gauged, or will its flows have to be "
              "reconstructed? A zero is an answer, not missing data.",
        "es": "Estaciones de aforo del Sandre en la cuenca, con su codigo y "
              "gestor. Responden a una pregunta simple : la cuenca esta "
              "aforada ? Un cero es una respuesta, no un dato ausente.",
        "pt": "Estacoes hidrometricas do Sandre na bacia, com codigo e "
              "gestor. Respondem a uma pergunta simples : a bacia e medida ? "
              "Um zero e uma resposta, nao um dado em falta.",
        "de": "Sandre-Pegelstationen im Gebiet, mit Code und Betreiber. Sie "
              "beantworten eine einfache Frage: ist das Gebiet bepegelt? "
              "Eine Null ist eine Antwort, kein fehlender Wert.",
    },

    # --- Execution --------------------------------------------------------
    "btn_report": {
        "fr": "Produire le rapport A4",
        "en": "Produce the A4 report",
        "es": "Generar el informe A4",
        "pt": "Gerar o relatorio A4",
        "de": "A4-Bericht erzeugen",
    },
    "report_tip": {
        "fr": "Disponible une fois un bassin versant delimite.",
        "en": "Available once a watershed has been delineated.",
        "es": "Disponible tras delimitar una cuenca.",
        "pt": "Disponivel apos delimitar uma bacia.",
        "de": "Verfugbar, sobald ein Einzugsgebiet abgegrenzt ist.",
    },
    "btn_view3d": {
        "fr": "Apercu 3D du relief",
        "en": "3D relief preview",
        "es": "Vista 3D del relieve",
        "pt": "Pre-visualizacao 3D do relevo",
        "de": "3D-Vorschau des Reliefs",
    },
    "view3d_tip": {
        "fr": "Bloc-diagramme du bassin, oriente a la souris. Disponible une "
              "fois un bassin delimite.",
        "en": "Block diagram of the catchment, rotated with the mouse. "
              "Available once a watershed has been delineated.",
        "es": "Bloque diagrama de la cuenca, girado con el raton. Disponible "
              "tras delimitar una cuenca.",
        "pt": "Bloco-diagrama da bacia, rodado com o rato. Disponivel apos "
              "delimitar uma bacia.",
        "de": "Blockbild des Einzugsgebiets, mit der Maus drehbar. Verfugbar, "
              "sobald ein Einzugsgebiet abgegrenzt ist.",
    },
    "view3d_hint": {
        "fr": "Cliquer-glisser pour tourner, molette pour zoomer. Le relief "
              "est exagere pour se voir.",
        "en": "Click and drag to rotate, wheel to zoom. Relief is exaggerated "
              "so that it shows.",
        "es": "Arrastrar para girar, rueda para ampliar. El relieve esta "
              "exagerado para verse.",
        "pt": "Arrastar para rodar, roda para ampliar. O relevo esta exagerado "
              "para se ver.",
        "de": "Ziehen zum Drehen, Rad zum Zoomen. Das Relief ist uberhoht, "
              "damit es sichtbar wird.",
    },
    "view3d_sw": {
        "fr": "Vue du sud-ouest",
        "en": "From the south-west",
        "es": "Desde el suroeste",
        "pt": "De sudoeste",
        "de": "Von Sudwesten",
    },
    "view3d_top": {
        "fr": "Vue du dessus",
        "en": "From above",
        "es": "Desde arriba",
        "pt": "De cima",
        "de": "Von oben",
    },
    "view3d_missing": {
        "fr": "Relief indisponible : matplotlib est absent, ou le calcul n'a "
              "pas conserve les altitudes.",
        "en": "Relief unavailable: matplotlib is missing, or the run did not "
              "keep the elevations.",
        "es": "Relieve no disponible: falta matplotlib, o el calculo no "
              "conservo las altitudes.",
        "pt": "Relevo indisponivel: falta o matplotlib, ou o calculo nao "
              "guardou as altitudes.",
        "de": "Relief nicht verfugbar: matplotlib fehlt, oder die Berechnung "
              "hat die Hohen nicht behalten.",
    },
    "preview_export": {
        "fr": "Exporter en PDF",
        "en": "Export to PDF",
        "es": "Exportar a PDF",
        "pt": "Exportar para PDF",
        "de": "Als PDF exportieren",
    },
    "btn_preview": {
        "fr": "Apercu et impression",
        "en": "Preview and print",
        "es": "Vista previa e impresion",
        "pt": "Pre-visualizar e imprimir",
        "de": "Vorschau und Druck",
    },
    "preview_tip": {
        "fr": "Affiche la page A4 sans rien enregistrer : on regarde, on "
              "imprime, ou on ferme.",
        "en": "Shows the A4 page without saving anything: look at it, print "
              "it, or close it.",
        "es": "Muestra la pagina A4 sin guardar nada: mirar, imprimir o "
              "cerrar.",
        "pt": "Mostra a pagina A4 sem gravar nada: ver, imprimir ou fechar.",
        "de": "Zeigt die A4-Seite, ohne etwas zu speichern: ansehen, drucken "
              "oder schliessen.",
    },
    "report_dialog": {
        "fr": "Enregistrer le rapport",
        "en": "Save the report",
        "es": "Guardar el informe",
        "pt": "Guardar o relatorio",
        "de": "Bericht speichern",
    },
    "report_done": {
        "fr": "✔ Rapport ecrit : {path}",
        "en": "✔ Report written: {path}",
        "es": "✔ Informe escrito: {path}",
        "pt": "✔ Relatorio gravado: {path}",
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
        "pt": "Relatorio gerado",
        "de": "Bericht erzeugt",
    },
    # Tient sur une ligne : le texte va dans un bandeau de la barre de
    # messages de QGIS, ou une question et des sauts de ligne n'ont plus lieu
    # d'etre - le bouton du bandeau pose la question a lui seul.
    "open_folder_ask": {
        "fr": "Rapport enregistre : {files}",
        "en": "Report saved: {files}",
        "es": "Informe guardado: {files}",
        "pt": "Relatorio gravado: {files}",
        "de": "Bericht gespeichert: {files}",
    },
    "open_folder": {
        "fr": "Ouvrir le dossier",
        "en": "Open the folder",
        "es": "Abrir la carpeta",
        "pt": "Abrir a pasta",
        "de": "Ordner offnen",
    },
    "open_folder_failed": {
        "fr": "⚠ Ouverture du dossier impossible : {path}",
        "en": "⚠ Could not open the folder: {path}",
        "es": "⚠ No se pudo abrir la carpeta: {path}",
        "pt": "⚠ Nao foi possivel abrir a pasta: {path}",
        "de": "⚠ Ordner konnte nicht geoffnet werden: {path}",
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
        "es": "⚠ falta matplotlib: informe generado sin graficos.",
        "pt": "⚠ matplotlib ausente: relatorio gerado sem graficos.",
        "de": "⚠ matplotlib fehlt: Bericht ohne Diagramme erzeugt.",
    },
    "layers_added": {
        "fr": "ℹ Couches creees en memoire dans le groupe {group}.",
        "en": "ℹ Memory layers created in group {group}.",
        "es": "ℹ Capas en memoria creadas en el grupo {group}.",
        "pt": "ℹ Camadas em memoria criadas no grupo {group}.",
        "de": "ℹ Speicherlayer in Gruppe {group} erstellt.",
    },
    "btn_run": {
        "fr": "Delimiter le bassin versant",
        "en": "Delineate the watershed",
        "es": "Delimitar la cuenca",
        "pt": "Delimitar a bacia",
        "de": "Einzugsgebiet abgrenzen",
    },
    "btn_cancel": {
        "fr": "Annuler le calcul",
        "en": "Cancel the computation",
        "es": "Cancelar el calculo",
        "pt": "Cancelar o calculo",
        "de": "Berechnung abbrechen",
    },
    "cancelled": {
        "fr": "Calcul annule.",
        "en": "Computation cancelled.",
        "es": "Calculo cancelado.",
        "pt": "Calculo cancelado.",
        "de": "Berechnung abgebrochen.",
    },
    "running_background": {
        "fr": "Calcul en cours en arriere-plan : QGIS reste utilisable.",
        "en": "Running in the background: QGIS stays usable.",
        "es": "Calculo en segundo plano: QGIS sigue utilizable.",
        "pt": "Calculo em segundo plano: o QGIS continua utilizavel.",
        "de": "Berechnung im Hintergrund: QGIS bleibt bedienbar.",
    },
    "ready": {
        "fr": "Pret.", "en": "Ready.", "es": "Listo.",
        "pt": "Pronto.", "de": "Bereit.",
    },
    "progress_fmt": {
        "fr": "%v / %m etape(s)", "en": "%v / %m step(s)",
        "es": "%v / %m etapa(s)", "pt": "%v / %m etapa(s)",
        "de": "%v / %m Schritt(e)",
    },
    "err_no_outlet": {
        "fr": "✘ Definissez d'abord un exutoire sur la carte.",
        "en": "✘ Please pick an outlet on the map first.",
        "es": "✘ Defina primero un punto de salida en el mapa.",
        "pt": "✘ Defina primeiro um exutorio no mapa.",
        "de": "✘ Bitte zuerst einen Auslass auf der Karte wahlen.",
    },
    "step_running": {
        "fr": "Etape {step}/{total} : {label}",
        "en": "Step {step}/{total}: {label}",
        "es": "Etapa {step}/{total}: {label}",
        "pt": "Etapa {step}/{total}: {label}",
        "de": "Schritt {step}/{total}: {label}",
    },
    "done_ok": {
        "fr": "✔ Bassin versant delimite en {seconds:.0f} s.",
        "en": "✔ Watershed delineated in {seconds:.0f} s.",
        "es": "✔ Cuenca delimitada en {seconds:.0f} s.",
        "pt": "✔ Bacia delimitada em {seconds:.0f} s.",
        "de": "✔ Einzugsgebiet in {seconds:.0f} s abgegrenzt.",
    },
    "done_error": {
        "fr": "✘ Echec : {error}",
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
        "de": "Einzugsgebiet zu gross",
    },
    "oversize_text": {
        "fr": "Ce bassin depasse ce que le traitement charge et n'a pas ete "
              "calcule.\n\nIl faudrait {count} troncons de reseau, quand la "
              "limite est de {budget}. Le bassin rendu serait tronque, sans "
              "que rien ne l'indique sur la carte.",
        "en": "This watershed exceeds what the run will load and was not "
              "computed.\n\nIt would take {count} network reaches against a "
              "limit of {budget}. The resulting basin would be clipped, with "
              "nothing on the map to show it.",
        "es": "Esta cuenca supera lo que el proceso carga y no se ha "
              "calculado.\n\nHarian falta {count} tramos de red, frente a un "
              "limite de {budget}. La cuenca resultante estaria truncada, sin "
              "ninguna senal en el mapa.",
        "pt": "Esta bacia excede o que o processamento carrega e nao foi "
              "calculada.\n\nSeriam precisos {count} trocos de rede, para um "
              "limite de {budget}. A bacia obtida ficaria truncada, sem "
              "qualquer indicacao no mapa.",
        "de": "Dieses Einzugsgebiet ubersteigt, was der Lauf ladt, und wurde "
              "nicht berechnet.\n\nNotig waren {count} Gewasserabschnitte bei "
              "einer Grenze von {budget}. Das Ergebnis ware abgeschnitten, "
              "ohne Hinweis in der Karte.",
    },
    "oversize_detail": {
        "fr": "Zone hydrographique : {zone}\n"
              "Deja parcouru : {upstream} troncons, {lineaire_km:.0f} km de "
              "lineaire, jusqu'a l'echelle du {scale}.\n\n"
              "Placer l'exutoire plus en amont donne un bassin juste en "
              "quelques secondes. Aller jusqu'a {max_count} troncons reste "
              "possible, mais le calcul se compte en minutes et la maille du "
              "MNT sera grossiere.",
        "en": "Hydrographic zone: {zone}\n"
              "Already walked: {upstream} reaches, {lineaire_km:.0f} km of "
              "network, up to the {scale} level.\n\n"
              "Moving the outlet further upstream gives a correct basin in "
              "seconds. Going to {max_count} reaches is still possible, but "
              "expect minutes and a coarse DEM cell size.",
        "es": "Zona hidrografica: {zone}\n"
              "Ya recorrido: {upstream} tramos, {lineaire_km:.0f} km de red, "
              "hasta la escala del {scale}.\n\n"
              "Situar el punto de salida mas aguas arriba da una cuenca "
              "correcta en segundos. Llegar a {max_count} tramos es posible, "
              "pero el calculo dura minutos y la malla del MDT sera gruesa.",
        "pt": "Zona hidrografica: {zone}\n"
              "Ja percorrido: {upstream} trocos, {lineaire_km:.0f} km de "
              "rede, ate a escala do {scale}.\n\n"
              "Colocar o exutorio mais a montante da uma bacia correta em "
              "segundos. Chegar a {max_count} trocos e possivel, mas o "
              "calculo demora minutos e a malha do MDT sera grosseira.",
        "de": "Hydrografische Zone: {zone}\n"
              "Bereits durchlaufen: {upstream} Abschnitte, "
              "{lineaire_km:.0f} km Netz, bis zur Ebene {scale}.\n\n"
              "Ein Auslass weiter oberhalb liefert in Sekunden ein korrektes "
              "Gebiet. Bis {max_count} Abschnitte ist es moglich, dauert aber "
              "Minuten bei grober Rasterweite.",
    },
    "oversize_zone_unknown": {
        "fr": "non identifiee", "en": "not identified",
        "es": "no identificada", "pt": "nao identificada",
        "de": "nicht ermittelt",
    },
    "oversize_go": {
        "fr": "Calculer quand meme (long)",
        "en": "Compute anyway (slow)",
        "es": "Calcular de todos modos (lento)",
        "pt": "Calcular mesmo assim (lento)",
        "de": "Trotzdem berechnen (langsam)",
    },
    "oversize_back": {
        "fr": "Choisir un autre exutoire",
        "en": "Pick another outlet",
        "es": "Elegir otro punto de salida",
        "pt": "Escolher outro exutorio",
        "de": "Anderen Auslass wahlen",
    },
    "oversize_status": {
        "fr": "✘ Bassin trop grand : calcul non lance.",
        "en": "✘ Watershed too large: not computed.",
        "es": "✘ Cuenca demasiado grande: no calculada.",
        "pt": "✘ Bacia demasiado grande: nao calculada.",
        "de": "✘ Einzugsgebiet zu gross: nicht berechnet.",
    },
    "oversize_log": {
        "fr": "\u26a0 Limite atteinte : {count} troncons seraient a charger, "
              "pour un maximum de {budget}. {upstream} troncons amont deja "
              "parcourus, {lineaire_km:.0f} km de lineaire.",
        "en": "\u26a0 Limit reached: {count} reaches would have to be "
              "loaded, against a maximum of {budget}. {upstream} upstream "
              "reaches already walked, {lineaire_km:.0f} km of network.",
        "es": "\u26a0 Limite alcanzado: habria que cargar {count} tramos, "
              "para un maximo de {budget}. {upstream} tramos aguas arriba ya "
              "recorridos, {lineaire_km:.0f} km de red.",
        "pt": "\u26a0 Limite atingido: seriam precisos {count} trocos, para "
              "um maximo de {budget}. {upstream} trocos a montante ja "
              "percorridos, {lineaire_km:.0f} km de rede.",
        "de": "\u26a0 Grenze erreicht: {count} Abschnitte waren zu laden, "
              "bei maximal {budget}. {upstream} Abschnitte oberhalb bereits "
              "durchlaufen, {lineaire_km:.0f} km Netz.",
    },
    "resuming": {
        "fr": "\u21bb Reprise du calcul : {dalles} dalles et {troncons} "
              "troncons deja en memoire, on repart de la.",
        "en": "\u21bb Resuming: {dalles} tiles and {troncons} reaches already "
              "in memory, carrying on from there.",
        "es": "\u21bb Reanudacion: {dalles} teselas y {troncons} tramos ya en "
              "memoria, se continua desde ahi.",
        "pt": "\u21bb Retoma: {dalles} mosaicos e {troncons} trocos ja em "
              "memoria, continua-se dai.",
        "de": "\u21bb Fortsetzung: {dalles} Kacheln und {troncons} Abschnitte "
              "bereits im Speicher, es geht dort weiter.",
    },
    "oversize_accepted": {
        "fr": "Calcul integral demande : le budget de troncons est releve, "
              "le calcul se poursuit.",
        "en": "Full computation requested: the reach budget is raised, the "
              "run carries on.",
        "es": "Calculo integral solicitado: se eleva el limite de tramos, el "
              "calculo continua.",
        "pt": "Calculo integral pedido: o limite de trocos e elevado, o "
              "calculo prossegue.",
        "de": "Vollstandige Berechnung angefordert: die Abschnittsgrenze wird "
              "angehoben, der Lauf geht weiter.",
    },

    # --- A propos ---------------------------------------------------------
    "about_title": {
        "fr": "A propos de BVLIP", "en": "About BVLIP",
        "es": "Acerca de BVLIP", "pt": "Acerca do BVLIP",
        "de": "Uber BVLIP",
    },
    "version_label": {
        "fr": "Version {version}", "en": "Version {version}",
        "es": "Version {version}", "pt": "Versao {version}",
        "de": "Version {version}",
    },
    "report_bug": {
        "fr": "Signaler un bug", "en": "Report a bug",
        "es": "Informar de un error", "pt": "Reportar um erro",
        "de": "Fehler melden",
    },
    "close": {
        "fr": "Fermer", "en": "Close", "es": "Cerrar",
        "pt": "Fechar", "de": "Schliessen",
    },
    "about_limits": {
        "fr": "Taille du bassin : la delimitation charge jusqu'a {guard} "
              "troncons de reseau, et jusqu'a {hard} si vous le demandez "
              "explicitement. Ces deux plafonds sont ceux que le plugin se "
              "fixe pour tenir en memoire, non des limites de la "
              "Geoplateforme. Au-dela, BVLIP refuse plutot que de rendre un "
              "bassin coupe au bord de l'emprise.",
        "en": "Catchment size: delineation loads up to {guard} network "
              "reaches, and up to {hard} if you explicitly ask. Both "
              "ceilings are the plugin's own, set to stay within memory, not "
              "Geoplateforme limits. Beyond them BVLIP refuses rather than "
              "return a basin clipped at the extent border.",
        "es": "Tamano de la cuenca: la delimitacion carga hasta {guard} "
              "tramos de red, y hasta {hard} si lo pide expresamente. Ambos "
              "limites son los que el complemento se fija para caber en "
              "memoria, no limites de la Geoplateforme. Mas alla, BVLIP "
              "rechaza en lugar de devolver una cuenca cortada.",
        "pt": "Tamanho da bacia: a delimitacao carrega ate {guard} trocos de "
              "rede, e ate {hard} se o pedir explicitamente. Ambos os "
              "limites sao os do proprio complemento, para caber em memoria, "
              "e nao limites da Geoplateforme. Para alem disso, o BVLIP "
              "recusa em vez de devolver uma bacia cortada.",
        "de": "Gebietsgrosse: die Abgrenzung ladt bis zu {guard} "
              "Gewasserabschnitte, auf ausdrucklichen Wunsch bis {hard}. "
              "Beide Grenzen setzt das Plugin selbst, um im Speicher zu "
              "bleiben; es sind keine Grenzen der Geoplateforme. Daruber "
              "lehnt BVLIP ab, statt ein am Rand abgeschnittenes Gebiet zu "
              "liefern.",
    },
    "data_credit": {
        "fr": "Donnees : RGE ALTI, BD TOPO, BD TOPAGE — IGN / Sandre",
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
