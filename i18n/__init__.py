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
        "fr": "Options", "en": "Options", "es": "Opciones",
        "pt": "Opcoes", "de": "Optionen",
    },
    "opt_metrics": {
        "fr": "Calculer les metriques morphometriques",
        "en": "Compute morphometric metrics",
        "es": "Calcular las metricas morfometricas",
        "pt": "Calcular as metricas morfometricas",
        "de": "Morphometrische Kennwerte berechnen",
    },
    "opt_refine": {
        "fr": "Recalculer a la maille la plus fine",
        "en": "Recompute at the finest cell size",
        "es": "Recalcular con la malla mas fina",
        "pt": "Recalcular com a malha mais fina",
        "de": "Mit der feinsten Zellgrosse neu berechnen",
    },
    "refine_tip": {
        "fr": "Sur un grand bassin, la maille est elargie faute de memoire. "
              "Cette option relance un second calcul sur le bassin recadre, "
              "ce qui permet de revenir a 5 m. Environ deux fois plus long, "
              "et sans effet sur la surface : n'active que si la pente ou le "
              "plus long cheminement comptent.",
        "en": "On a large catchment the cell size is enlarged for lack of "
              "memory. This option runs a second pass on the cropped basin, "
              "back down to 5 m. About twice as long, and it does not change "
              "the area: use it when slope or the longest flow path matter.",
        "es": "En una cuenca grande la malla se amplia por falta de memoria. "
              "Esta opcion relanza un segundo calculo sobre la cuenca "
              "recortada, hasta 5 m. Dura el doble y no cambia la superficie.",
        "pt": "Numa bacia grande a malha e alargada por falta de memoria. "
              "Esta opcao repete o calculo sobre a bacia recortada, ate 5 m. "
              "Demora o dobro e nao altera a area.",
        "de": "Bei einem grossen Einzugsgebiet wird die Zellgrosse aus "
              "Speichermangel vergrossert. Diese Option rechnet ein zweites "
              "Mal auf dem zugeschnittenen Gebiet, zuruck auf 5 m. Etwa "
              "doppelt so lange, ohne die Flache zu andern.",
    },
    "opt_landcover": {
        "fr": "Analyser l'occupation du sol",
        "en": "Analyse land cover",
        "es": "Analizar la ocupacion del suelo",
        "pt": "Analisar a ocupacao do solo",
        "de": "Landbedeckung analysieren",
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
    "open_folder_ask": {
        "fr": "Le rapport est enregistre :\n\n{files}\n\nOuvrir le dossier ?",
        "en": "The report has been saved:\n\n{files}\n\nOpen the folder?",
        "es": "El informe ha sido guardado:\n\n{files}\n\n¿Abrir la carpeta?",
        "pt": "O relatorio foi gravado:\n\n{files}\n\nAbrir a pasta?",
        "de": "Der Bericht wurde gespeichert:\n\n{files}\n\nOrdner offnen?",
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
