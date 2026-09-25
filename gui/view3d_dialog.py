# -*- coding: utf-8 -*-
"""Fenetre d'apercu du relief, tournante a la souris.

La vue principale est la page WebGL de l'export HTML, affichee dans un
navigateur embarque (gui/web3d.py) et pilotee par le panneau. Tout ce qui
suit sur matplotlib ne vaut plus que pour le mode de secours, quand QGIS n'a
aucun moteur web.

C'est le meme bloc-diagramme que celui du rapport - la meme fonction le
dessine - mais pose sur un canevas Qt plutot que dans une image : on tourne le
bassin, on l'incline, on le regarde du dessus.

Le moteur 3D de QGIS aurait ete plus beau, mais il n'est pas pilotable depuis
Python : Qgs3DMapCanvas s'instancie bien seul, mais n'expose aucune methode
pour lui poser des reglages de scene (verifie en console sur QGIS 3.44 -
mapSettings() renvoie toujours None, aucun setMapSettings() n'existe cote
Python). matplotlib, lui, est deja la pour les graphiques du rapport et ne
demande aucune carte graphique.

La contrepartie est le prix d'une image : matplotlib redessine toute la
surface a chaque mouvement. La grille est donc allegee pour cette vue, bien
plus que pour l'image du rapport, sans quoi la rotation serait insupportable.
Le bouton haute qualite repasse a la grille complete pour un instant, une fois
la rotation arretee - typiquement avant un export.

Les commandes vivent dans un panneau lateral plutot qu'en rangees au-dessus
du canevas : a mesure que l'habillage et l'export s'y sont ajoutes, une seule
bande horizontale devenait illisible. Un panneau permet de grouper par
fonction (vue, habillage, export) comme le ferait un outil de modelisation
3D, et les boutons de vue en croix retrouvent leur disposition de boussole -
plus rapide a lire qu'une rangee de sigles.

L'habillage se coche plutot qu'il ne se choisit : BD Foret et parcelles
agricoles peuvent s'empiler, chacune visible la ou l'autre n'a rien a
montrer - QGIS composite les couches lui-meme au rendu (core/drape.py), il
n'y a pas besoin de melanger les pixels a la main. Une legende a gauche du
canevas reprend les memes couleurs, categorie par categorie, pour les
habillages actifs.

La rotation garde sa fluidite quelle que soit la definition choisie : le
temps d'un cliquer-glisser, une surface deux fois plus legere remplace la
surface fine (voir coarse_decimate dans relief_figure), et la fine revient
au relachement. Les curseurs (exageration, opacite) ne redessinent
de meme qu'au relachement : un redessin par cran de curseur figeait la
fenetre des que la definition montait.

Les exports 3D (.glb, page HTML) ne reprennent pas la grille de l'apercu
mais une texture bien plus fine, ou le chevelu et l'exutoire sont peints -
voir report/export3d.py.
"""

from qgis.PyQt.QtCore import Qt, QUrl
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtWidgets import (
    QApplication, QDialog, QFileDialog, QFrame,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QMessageBox, QPushButton, QScrollArea, QSizePolicy, QSlider,
    QVBoxLayout, QWidget,
)

from ..i18n import tr
from ..report import charts, export3d

# Points de vue proposes, en disposition de boussole dans le panneau (voir
# _build_view_group) : les quatre points cardinaux intermediaires, qui
# donnent chacun du volume au relief sous un angle different, et le dessus,
# qui redonne la forme du bassin telle qu'on la lit sur une carte.
VIEWS = {
    "sw": (42.0, -125.0),
    "se": (42.0, -55.0),
    "ne": (42.0, 55.0),
    "nw": (42.0, 125.0),
    "top": (89.0, -90.0),
}

# Bornes du curseur d'exageration verticale, en dixiemes pour un pas de 0.1x.
# Au-dela de 10x le relief perd toute lisibilite - c'est deja enorme pour un
# bassin dont le denivele ne fait souvent qu'une fraction de l'etendue.
EXAGGERATION_MIN = 10
EXAGGERATION_MAX = 100
EXAGGERATION_DEFAULT = 22

# Valeurs en un clic sous les curseurs d'exageration et d'opacite.
EXAGGERATION_PRESETS = (1.5, 2, 2.5, 5)
OPACITY_PRESETS = (90, 75, 50)

PANEL_WIDTH = 270
LEGEND_WIDTH = 210

# Zoom par les boutons dedies : la molette de matplotlib zoome deja sur les
# vues 3D dans les versions recentes, mais pas de facon fiable une fois
# integree a un canevas Qt sans barre d'outils - des boutons marchent partout.
ZOOM_STEP = 1.25
ZOOM_MIN = 0.3
ZOOM_MAX = 4.0

# Definition de la grille : 5 crans, du plus fluide (1, l'allegement adapte
# de live_decimate) au plus net (5, jusqu'a la pleine resolution). Remplace
# l'ancien bouton "Haute qualite" a un seul palier fixe par un reglage
# progressif - on monte tant que la rotation reste agreable, pas plus.
DEFINITION_MIN = 1
DEFINITION_MAX = 5
DEFINITION_DEFAULT = 2

# Habillages disponibles, dans leur ordre d'empilement de depart - du dessus
# vers le dessous, comme une legende. Cet ordre n'est plus fige : le panneau
# laisse le remonter ou le descendre, et chaque habillage porte sa propre
# opacite. La table ne fait donc que proposer un empilement de depart, celui
# qui se lit le mieux sans rien regler.
#
# Corine n'a pas de cle de layers{} - il n'est pas une couche du projet, il se
# telecharge a la demande (voir _layers_for). Le relief en niveaux de gris
# n'en a pas non plus, mais pour une autre raison : il n'est pas rendu par
# QGIS du tout, il est fabrique a partir de la grille d'altitudes (voir
# _grey_base).
#
# "Agriculture (PAC)" regroupe RPG et bio sous une seule case : ce sont deux
# couches distinctes cote donnees (le rapport les detaille chacune dans sa
# propre section), mais un seul et meme sujet cote habillage - la declaration
# PAC, bio y compris. Le bio est liste avant le parcellaire general pour
# rester visible par-dessus lui, la ou les deux se recouvrent.
#
# Le reseau hydrographique est place en tete : c'est un trait fin, colore
# selon la permanence de l'ecoulement (voir _style_streams) - il doit rester
# visible par-dessus les habillages en aplat plutot que de se faire recouvrir
# par eux. Il double le chevelu bleu deja drape sur le relief (charts.py),
# mais celui-ci n'en montre que l'ordre de Strahler, pas la permanence.
#
# L'orthophoto IGN vient en avant-derniere : image pleine, sans transparence,
# elle masquerait tout ce qui serait dessous - seul le relief gris, qui n'a
# rien a montrer sous elle, y est range. Comme Corine, elle n'est pas une
# couche du projet : la couche WMTS s'ouvre au premier cochage.
#
# Le relief gris ferme la marche : c'est un fond, il n'a rien a masquer.
HABILLAGE_OPTIONS = (
    ("reseau", ("reseau",), "view3d_habillage_reseau"),
    ("agriculture", ("bio", "parcelles"), "view3d_habillage_agriculture"),
    ("foret", ("foret",), "view3d_habillage_foret"),
    ("corine", (), "view3d_habillage_corine"),
    ("ortho", (), "view3d_habillage_ortho"),
    ("relief_gris", (), "view3d_habillage_relief_gris"),
)

# Cle de l'habillage fabrique et non rendu par QGIS.
RELIEF_GRIS = "relief_gris"

# Gris de depart du fond de relief. Il n'est pas dessine tel quel : le
# bloc-diagramme l'ombre ensuite avec les altitudes (shade_rgb dans charts),
# et c'est cet ombrage qui en fait un relief en niveaux de gris. Un gris clair
# laisse la place aux deux cotes - les versants a l'ombre s'assombrissent sans
# virer au noir, ceux au soleil s'eclaircissent sans saturer.
GREY_LEVEL = 205


class View3dDialog(QDialog):
    """Bloc-diagramme du bassin, oriente a la souris."""

    def __init__(self, relief, lang, parent=None, layers=None):
        super().__init__(parent)
        self.relief = relief
        self.lang = lang
        self.layers = layers or {}
        self.exaggeration = EXAGGERATION_DEFAULT / 10.0
        self.definition = DEFINITION_DEFAULT
        self.zoom = 1.0
        self.light_azimuth = charts.LIGHT_AZIMUTH
        self.light_altitude = charts.LIGHT_ALTITUDE
        self.palette = charts.RELIEF_CMAP
        self.show_network = True
        self.show_outlet = True
        self.show_title = True
        # La vue par defaut est de biais (sud-ouest) : la ligne de partage
        # des eaux (voir relief_figure/show_contour) part donc masquee, comme
        # dans toutes les vues de biais - seul "Dessus" la fait apparaitre.
        self.show_contour = False
        # Etat des habillages : un dictionnaire par entree, dans l'ordre
        # d'empilement courant (le premier est dessus). L'utilisateur peut
        # remonter, descendre, cocher et regler l'opacite de chacun.
        self.habillages = [
            {"key": key, "label_key": label_key, "checked": False,
             "opacity": 100}
            for key, layer_keys, label_key in HABILLAGE_OPTIONS
            if not layer_keys or any(
                (layers or {}).get(lk) is not None for lk in layer_keys
            )
        ]
        self._rendered = {}           # (cle, facteur) -> calque RVBA rendu
        self._corine_layer = None     # telechargee une fois, gardee ensuite
        self._ortho_layer = None      # couche WMTS, ouverte une fois
        self.setWindowTitle(tr("btn_view3d", lang))
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )
        self.resize(1200, 760)

        self.axes = None
        self.figure = None
        self.canvas = None
        self.web = None               # WebReliefView, si un moteur web existe
        self._web_state = None        # etat du dernier chargement de la page
        self._build_web_view()
        if self.web is None:
            self._build_canvas_object()

        root = QHBoxLayout()
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        if not self._ready:
            root.addWidget(QLabel(tr("view3d_missing", lang)))
        else:
            self.legend_panel = self._build_legend_panel()
            self.legend_panel.setVisible(False)
            root.addWidget(self.legend_panel)

            if self.web is not None:
                root.addWidget(self.web, 1)
            else:
                viewport = QVBoxLayout()
                viewport.setSpacing(4)
                viewport.addWidget(self.canvas, 1)
                viewport.addWidget(QLabel(tr("view3d_hint", lang)))
                root.addLayout(viewport, 1)
            root.addWidget(self._build_panel())
        self.setLayout(root)
        self.finished.connect(self._cleanup_web)
        if self.web is not None:
            self._refresh_web()

    # ------------------------------------------------------------- Montage

    @property
    def _ready(self):
        """Vrai si le relief s'affiche, par la page web ou par matplotlib."""
        return self.web is not None or self.axes is not None

    def _build_web_view(self):
        """Navigateur embarque qui affiche la page 3D de l'export HTML.

        C'est la vue principale : WebGL tourne le relief a pleine
        definition, sans le prix d'un redessin matplotlib a chaque
        mouvement. L'apercu matplotlib ne sert plus que de secours, quand
        QGIS n'a aucun moteur web (voir gui/web3d.py).
        """
        from .web3d import WebReliefView

        view = WebReliefView()
        if view.available:
            self.web = view

    def _current_web_state(self):
        """Ce qui change la texture de la page, donc impose de la recharger.

        L'exageration, le point de vue et le zoom n'y sont pas : ils se
        pilotent dans la page sans la recharger (voir window.bvlip).
        """
        return (
            tuple((e["key"], e["checked"], e["opacity"])
                  for e in self.habillages),
            self.palette, self.light_azimuth, self.light_altitude,
            self.show_network, self.show_outlet, self.show_contour,
        )

    def _refresh_web(self):
        """(Re)charge la page si ce qui colore la texture a change."""
        if self.web is None:
            return
        state = self._current_web_state()
        if state == self._web_state:
            return
        self._set_status(tr("view3d_web_loading", self.lang))
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            page = export3d.html_page(
                self.relief, self.exaggeration, self._fine_texture(),
                self._html_texts(),
            )
            if page is None:
                self._set_status(tr("view3d_missing", self.lang))
                return
            self.web.show_page(page)
            self._web_state = state
            self._set_status("")
        except Exception as exc:
            self._set_status(tr("done_error", self.lang, error=exc))
        finally:
            QApplication.restoreOverrideCursor()

    def _cleanup_web(self, *_args):
        if self.web is not None:
            self.web.cleanup()

    def _build_canvas_object(self):
        """Cree la figure matplotlib et son canevas Qt, ou laisse None."""
        try:
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
        except ImportError:      # matplotlib d'avant 3.5
            try:
                from matplotlib.backends.backend_qt5agg import (
                    FigureCanvasQTAgg,
                )
            except ImportError:
                return
        from matplotlib.figure import Figure

        # Figure construite a la main, sans passer par pyplot : c'est la seule
        # facon d'attacher un canevas Qt sans que matplotlib n'ouvre en plus sa
        # propre fenetre.
        self.figure = Figure(figsize=(8.5, 6.5), facecolor="white")
        self.axes = charts.relief_figure(
            self.relief, self.figure, **self._figure_options()
        )
        if self.axes is None:
            self.figure = None
            return
        self._tune_mouse()
        self.canvas = FigureCanvasQTAgg(self.figure)
        # Branches une fois pour toutes : ils vivent sur le canevas, que le
        # redessin (figure.clear) ne remplace pas.
        self.canvas.mpl_connect("button_press_event", self._on_press)
        self.canvas.mpl_connect("button_release_event", self._on_release)
        self.canvas.mpl_connect("scroll_event", self._on_scroll)

    def _figure_options(self, view=None):
        """Parametres de relief_figure tires de l'etat de la fenetre."""
        options = dict(
            exaggeration=self.exaggeration,
            decimate=self._current_decimate(),
            coarse_decimate=self._rotation_decimate(),
            show_contour=self.show_contour,
            show_network=self.show_network,
            show_outlet=self.show_outlet,
            show_title=self.show_title,
            light_azimuth=self.light_azimuth,
            light_altitude=self.light_altitude,
            cmap=self.palette,
        )
        if view is not None:
            options["elevation"], options["azimuth"] = view
        return options

    def _tune_mouse(self):
        """Laisse a matplotlib la rotation et le deplacement, pas le zoom.

        Le zoom au clic droit de matplotlib changerait les limites d'axes
        dans le dos de self.zoom : le suivant repartirait d'ailleurs. Le zoom
        passe donc par la molette et les boutons, qui tiennent le compte.
        """
        try:
            self.axes.mouse_init(rotate_btn=1, pan_btn=2, zoom_btn=[])
        except TypeError:        # pragma: no cover - matplotlib sans zoom_btn
            pass

    def _build_legend_panel(self):
        """Colonne de gauche, vide tant qu'aucun habillage n'est coche."""
        group = QGroupBox(tr("view3d_legend_title", self.lang))
        group.setFixedWidth(LEGEND_WIDTH)
        outer = QVBoxLayout()
        outer.setContentsMargins(4, 4, 4, 4)

        self.legend_content = QWidget()
        self.legend_layout = QVBoxLayout()
        self.legend_layout.setSpacing(6)
        self.legend_layout.addStretch(1)
        self.legend_content.setLayout(self.legend_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(self.legend_content)
        outer.addWidget(scroll)

        group.setLayout(outer)
        return group

    def _build_panel(self):
        """Panneau lateral : vue, habillage, export.

        Plus de reglage d'eclairage : le soleil et le nuancier restent ceux
        du rapport (charts.LIGHT_AZIMUTH, LIGHT_ALTITUDE, RELIEF_CMAP).

        Les groupes defilent dans une zone a ascenseur : a quatre, ils ne
        tiennent plus sur un petit ecran. Le bouton Fermer reste hors de la
        zone, toujours visible.
        """
        panel = QWidget()
        panel.setFixedWidth(PANEL_WIDTH)
        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(6)

        content = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 6, 0)
        layout.setSpacing(10)
        layout.addWidget(self._build_view_group())
        layout.addWidget(self._build_habillage_group())
        layout.addWidget(self._build_export_group())
        layout.addStretch(1)
        content.setLayout(layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        # Largeur du contenu calee sur la place laissee par l'ascenseur :
        # sans cela, il se glisse sous l'ascenseur et rogne la colonne de
        # droite des groupes.
        content.setFixedWidth(
            PANEL_WIDTH - scroll.verticalScrollBar().sizeHint().width() - 2
        )
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

        close = QPushButton(tr("close", self.lang))
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.setMinimumHeight(30)
        close.clicked.connect(self.accept)
        outer.addWidget(close)

        panel.setLayout(outer)
        return panel

    def _build_view_group(self):
        """Boutons de vue en croix de boussole - NO/dessus/NE, SO/·/SE.

        Une disposition spatiale se lit plus vite qu'une rangee de sigles :
        la main clique dans la direction voulue plutot que de lire un texte.
        """
        group = QGroupBox(tr("view3d_view_group", self.lang))
        grid = QGridLayout()
        grid.setSpacing(4)

        self.btn_nw = QPushButton(tr("view3d_nw_short", self.lang))
        self.btn_top = QPushButton(tr("view3d_top_short", self.lang))
        self.btn_ne = QPushButton(tr("view3d_ne_short", self.lang))
        self.btn_sw = QPushButton(tr("view3d_sw_short", self.lang))
        self.btn_se = QPushButton(tr("view3d_se_short", self.lang))

        self.btn_nw.setToolTip(tr("view3d_nw", self.lang))
        self.btn_top.setToolTip(tr("view3d_top", self.lang))
        self.btn_ne.setToolTip(tr("view3d_ne", self.lang))
        self.btn_sw.setToolTip(tr("view3d_sw", self.lang))
        self.btn_se.setToolTip(tr("view3d_se", self.lang))

        self.btn_nw.clicked.connect(lambda: self._look("nw"))
        self.btn_top.clicked.connect(lambda: self._look("top"))
        self.btn_ne.clicked.connect(lambda: self._look("ne"))
        self.btn_sw.clicked.connect(lambda: self._look("sw"))
        self.btn_se.clicked.connect(lambda: self._look("se"))

        view_buttons = (
            self.btn_nw, self.btn_top, self.btn_ne, self.btn_sw, self.btn_se,
        )
        for button in view_buttons:
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setMinimumHeight(32)
            button.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
            )
        grid.addWidget(self.btn_nw, 0, 0)
        grid.addWidget(self.btn_top, 0, 1)
        grid.addWidget(self.btn_ne, 0, 2)
        grid.addWidget(self.btn_sw, 1, 0)
        grid.addWidget(self.btn_se, 1, 2)

        zoom_row = QHBoxLayout()
        zoom_row.setSpacing(4)
        self.btn_zoom_out = QPushButton(tr("view3d_zoom_out", self.lang))
        self.btn_zoom_out.clicked.connect(lambda: self._zoom(1 / ZOOM_STEP))
        self.btn_zoom_in = QPushButton(tr("view3d_zoom_in", self.lang))
        self.btn_zoom_in.clicked.connect(lambda: self._zoom(ZOOM_STEP))
        for button in (self.btn_zoom_out, self.btn_zoom_in):
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setMinimumHeight(28)
        zoom_row.addWidget(self.btn_zoom_out)
        zoom_row.addWidget(self.btn_zoom_in)

        definition_row = QHBoxLayout()
        definition_row.setSpacing(4)
        definition_row.addWidget(QLabel(tr("view3d_definition", self.lang)))
        definition_row.addStretch(1)
        self.btn_definition_minus = QPushButton("−")
        self.btn_definition_minus.clicked.connect(
            lambda: self._change_definition(-1)
        )
        self.label_definition = QLabel(
            "{0}/{1}".format(self.definition, DEFINITION_MAX)
        )
        self.label_definition.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_definition.setMinimumWidth(28)
        self.btn_definition_plus = QPushButton("+")
        self.btn_definition_plus.clicked.connect(
            lambda: self._change_definition(1)
        )
        for button in (self.btn_definition_minus, self.btn_definition_plus):
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setMinimumHeight(26)
            button.setFixedWidth(36)
        definition_row.addWidget(self.btn_definition_minus)
        definition_row.addWidget(self.label_definition)
        definition_row.addWidget(self.btn_definition_plus)

        column = QVBoxLayout()
        column.addLayout(grid)
        column.addLayout(zoom_row)
        # La definition n'allege que le dessin matplotlib : la page web
        # affiche toujours la grille entiere. La ligne n'existe donc qu'en
        # mode de secours, sans moteur web.
        if self.web is None:
            column.addLayout(definition_row)
        group.setLayout(column)

        definition_buttons = (self.btn_definition_minus, self.btn_definition_plus)
        for button in (
            view_buttons + (self.btn_zoom_out, self.btn_zoom_in)
            + definition_buttons
        ):
            button.setEnabled(self._ready)
        return group

    def _build_habillage_group(self):
        """Liste d'habillages empilables : ordre et opacite se reglent ici.

        Une liste plutot que des cases alignees : l'ordre compte desormais -
        c'est celui de l'empilement - et une liste le montre en le rendant
        manipulable, ce qu'une colonne de cases ne sait pas faire.
        """
        group = QGroupBox(tr("view3d_habillage", self.lang))
        column = QVBoxLayout()

        self.list_habillage = QListWidget()
        self.list_habillage.setMaximumHeight(120)
        self.list_habillage.setEnabled(self._ready)
        self.list_habillage.itemChanged.connect(self._on_habillage_item_changed)
        self.list_habillage.currentRowChanged.connect(
            self._on_habillage_row_changed
        )
        column.addWidget(self.list_habillage)

        move_row = QHBoxLayout()
        move_row.setSpacing(4)
        self.btn_up = QPushButton(tr("view3d_move_up", self.lang))
        self.btn_up.setToolTip(tr("view3d_move_up_tip", self.lang))
        self.btn_up.clicked.connect(lambda: self._move_habillage(-1))
        self.btn_down = QPushButton(tr("view3d_move_down", self.lang))
        self.btn_down.setToolTip(tr("view3d_move_down_tip", self.lang))
        self.btn_down.clicked.connect(lambda: self._move_habillage(1))
        for button in (self.btn_up, self.btn_down):
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setMinimumHeight(26)
            button.setEnabled(self._ready)
            move_row.addWidget(button)
        column.addLayout(move_row)

        opacity_row = QHBoxLayout()
        opacity_row.addWidget(QLabel(tr("view3d_opacity", self.lang)))
        opacity_row.addStretch(1)
        self.label_opacity = QLabel("—")
        self.label_opacity.setMinimumWidth(38)
        opacity_row.addWidget(self.label_opacity)
        column.addLayout(opacity_row)

        self.slider_opacity = QSlider(Qt.Orientation.Horizontal)
        self.slider_opacity.setMinimum(0)
        self.slider_opacity.setMaximum(100)
        self.slider_opacity.setValue(100)
        self.slider_opacity.setEnabled(False)
        self.slider_opacity.valueChanged.connect(self._on_opacity_changed)
        self.slider_opacity.sliderReleased.connect(self._on_opacity_released)
        column.addWidget(self.slider_opacity)
        row, self.opacity_presets = self._preset_row(
            OPACITY_PRESETS, "{0} %", self.slider_opacity.setValue)
        for button in self.opacity_presets:
            button.setEnabled(False)
        column.addLayout(row)

        self._refresh_habillage_list()

        exag_row = QHBoxLayout()
        exag_row.addWidget(QLabel(tr("view3d_exaggeration", self.lang)))
        exag_row.addStretch(1)
        self.label_exaggeration = QLabel("{0:.1f}×".format(self.exaggeration))
        exag_row.addWidget(self.label_exaggeration)
        column.addLayout(exag_row)

        self.slider_exaggeration = QSlider(Qt.Orientation.Horizontal)
        self.slider_exaggeration.setMinimum(EXAGGERATION_MIN)
        self.slider_exaggeration.setMaximum(EXAGGERATION_MAX)
        self.slider_exaggeration.setValue(EXAGGERATION_DEFAULT)
        self.slider_exaggeration.setSingleStep(1)
        self.slider_exaggeration.setEnabled(self._ready)
        self.slider_exaggeration.valueChanged.connect(
            self._on_exaggeration_changed
        )
        self.slider_exaggeration.sliderReleased.connect(self._redraw)
        column.addWidget(self.slider_exaggeration)
        row, buttons = self._preset_row(
            EXAGGERATION_PRESETS, "×{0:g}",
            lambda value: self.slider_exaggeration.setValue(int(round(value * 10))))
        for button in buttons:
            button.setEnabled(self._ready)
        column.addLayout(row)

        group.setLayout(column)
        return group

    @staticmethod
    def _preset_row(values, text, apply):
        """Rangee de petits boutons de valeurs toutes faites sous un curseur.

        Le curseur reste pour le reglage fin ; les boutons donnent en un clic
        les valeurs qu'on cherche le plus souvent.
        """
        row = QHBoxLayout()
        row.setSpacing(3)
        buttons = []
        for value in values:
            button = QPushButton(text.format(value))
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setFixedHeight(22)
            button.setStyleSheet("QPushButton { padding: 0 4px; font-size: 11px; }")
            button.clicked.connect(lambda _checked=False, v=value: apply(v))
            row.addWidget(button)
            buttons.append(button)
        return row, buttons

    def _build_export_group(self):
        group = QGroupBox(tr("view3d_export_group", self.lang))
        column = QVBoxLayout()

        self.btn_export_image = QPushButton(tr("view3d_export", self.lang))
        self.btn_export_image.clicked.connect(self._export_image)
        self.btn_export_mesh = QPushButton(tr("view3d_export_mesh", self.lang))
        self.btn_export_mesh.setToolTip(
            tr("view3d_export_mesh_tip", self.lang))
        self.btn_export_mesh.clicked.connect(self._export_mesh)
        self.btn_export_html = QPushButton(tr("view3d_export_html", self.lang))
        self.btn_export_html.setToolTip(
            tr("view3d_export_html_tip", self.lang))
        self.btn_export_html.clicked.connect(self._export_html)
        for button in (self.btn_export_image, self.btn_export_mesh,
                       self.btn_export_html):
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setMinimumHeight(28)
            button.setEnabled(self._ready)
            column.addWidget(button)

        self.label_status = QLabel("")
        self.label_status.setWordWrap(True)
        column.addWidget(self.label_status)

        group.setLayout(column)
        return group

    # -------------------------------------------------------------- Actions

    def _look(self, name):
        """Ramene la vue a un point de vue nomme.

        Redessine plutot qu'un simple view_init : la ligne de crete rouge
        n'apparait que de dessus (voir show_contour dans relief_figure), or
        elle est posee au dessin et ne peut pas se cacher apres coup sans
        reconstruire la figure.
        """
        if self.web is not None:
            # La page tourne sa camera elle-meme, sans recharger : la ligne
            # de crete, peinte dans la texture, y reste telle quelle.
            self.web.run_js("window.bvlip && window.bvlip.view({0}, {1})"
                            .format(*VIEWS[name]))
            return
        if self.axes is None or self.canvas is None:
            return
        self.show_contour = name == "top"
        self._redraw(view=VIEWS[name])

    def _zoom(self, factor):
        if self.web is not None:
            self.web.run_js(
                "window.bvlip && window.bvlip.zoom({0})".format(factor))
            return
        self.zoom = min(ZOOM_MAX, max(ZOOM_MIN, self.zoom * factor))
        self._apply_zoom()

    def _apply_zoom(self):
        """Reduit les limites 3D autour de leur centre, dans les mailles.

        Le zoom porte sur les limites d'axes (xlim3d/ylim3d/zlim3d), pas sur
        la camera : elles persistent d'une vue a l'autre (view_init ne les
        touche pas), donc pas besoin de reappliquer le zoom a chaque clic sur
        un point de vue - seul un redessin (_redraw) les reinitialise.
        """
        if self.axes is None or self.canvas is None:
            return
        import numpy as np

        grid = np.asarray(self.relief["grid"])
        x = np.asarray(self.relief["x"])
        y = np.asarray(self.relief["y"])
        low, high = float(np.nanmin(grid)), float(np.nanmax(grid))

        cx, hx = (x.min() + x.max()) / 2.0, (x.max() - x.min()) / 2.0 / self.zoom
        cy, hy = (y.min() + y.max()) / 2.0, (y.max() - y.min()) / 2.0 / self.zoom
        cz, hz = (low + high) / 2.0, max(high - low, 1e-6) / 2.0 / self.zoom

        self.axes.set_xlim3d(cx - hx, cx + hx)
        self.axes.set_ylim3d(cy - hy, cy + hy)
        self.axes.set_zlim3d(cz - hz, cz + hz)
        self.canvas.draw_idle()

    def _on_exaggeration_changed(self, value):
        """Reconstruit le bloc-diagramme a la nouvelle exageration.

        L'angle de vue courant est repris tel quel : ajuster l'exageration
        ne doit pas faire perdre l'orientation ou l'utilisateur venait de se
        placer.
        """
        self.exaggeration = value / 10.0
        self.label_exaggeration.setText("{0:.1f}×".format(
            self.exaggeration
        ))
        if self.web is not None:
            self.web.run_js("window.bvlip && window.bvlip.exaggeration({0})"
                            .format(self.exaggeration))
            return
        if not self.slider_exaggeration.isSliderDown():
            self._redraw()     # clavier ou clic : un seul cran, on redessine

    def _change_definition(self, step):
        """Monte ou descend d'un cran la definition de la grille affichee.

        Chaque cran retire un peu de l'allegement adaptatif de
        live_decimate, jusqu'a la pleine resolution au cran 5 - a monter tant
        que la rotation reste agreable, plus lente a mesure qu'on approche du
        plafond.
        """
        self.definition = min(
            DEFINITION_MAX, max(DEFINITION_MIN, self.definition + step)
        )
        self.label_definition.setText(
            "{0}/{1}".format(self.definition, DEFINITION_MAX)
        )
        self._redraw()

    def _current_decimate(self):
        base = charts.live_decimate(self.relief)
        return max(1, base - (self.definition - 1))

    def _rotation_decimate(self):
        """Pas de la surface montree pendant une rotation a la souris.

        Une maille sur deux de la surface choisie, sans jamais descendre
        sous l'allegement de base (live_decimate) : la rotation reste
        proche de l'image a l'arret. Une surface bien plus grossiere
        restait visible plusieurs secondes apres le relachement, le temps
        que la fine se redessine, et l'apercu paraissait pixelise.
        """
        return min(charts.live_decimate(self.relief),
                   self._current_decimate() * 2)

    # ------------------------------------------------ Souris et affichage

    def _on_press(self, event):
        """Passe a la surface allegee le temps d'une rotation."""
        if event.inaxes is not self.axes or event.button != 1:
            return
        fine, coarse = getattr(self.axes, "bvlip_surfaces", (None, None))
        if coarse is not None:
            fine.set_visible(False)
            coarse.set_visible(True)

    def _on_release(self, event):
        """Revient a la surface fine, une fois la rotation arretee."""
        if self.axes is None:
            return
        fine, coarse = getattr(self.axes, "bvlip_surfaces", (None, None))
        if coarse is not None and coarse.get_visible():
            coarse.set_visible(False)
            fine.set_visible(True)
            self.canvas.draw_idle()

    def _on_scroll(self, event):
        """Molette : zoom, d'un cran de bouton par cran de molette."""
        if self.axes is None:
            return
        step = getattr(event, "step", 0) or (
            1 if event.button == "up" else -1
        )
        self._zoom(ZOOM_STEP ** step)

    # ---------------------------------------------------------- Habillages

    def _refresh_habillage_list(self):
        """Reecrit la liste a partir de self.habillages, ordre compris."""
        current = self.list_habillage.currentRow()
        self.list_habillage.blockSignals(True)
        self.list_habillage.clear()
        for entry in self.habillages:
            item = QListWidgetItem(tr(entry["label_key"], self.lang))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked if entry["checked"]
                else Qt.CheckState.Unchecked
            )
            if entry["checked"] and entry["opacity"] < 100:
                item.setText("{0}  ({1} %)".format(
                    item.text(), entry["opacity"]))
            self.list_habillage.addItem(item)
        self.list_habillage.blockSignals(False)
        if 0 <= current < len(self.habillages):
            self.list_habillage.setCurrentRow(current)

    def _on_habillage_item_changed(self, item):
        row = self.list_habillage.row(item)
        if not 0 <= row < len(self.habillages):
            return
        checked = item.checkState() == Qt.CheckState.Checked
        entry = self.habillages[row]
        if entry["checked"] == checked:
            return
        entry["checked"] = checked

        self._set_status("")
        if checked:
            try:
                self._render_habillage(entry["key"])
            except Exception as exc:
                self._set_status(
                    tr("view3d_habillage_error", self.lang, error=exc)
                )
                entry["checked"] = False
        self._refresh_habillage_list()
        self._update_legend()
        self._redraw()

    def _on_habillage_row_changed(self, row):
        """Le curseur d'opacite suit la ligne selectionnee."""
        if not 0 <= row < len(self.habillages):
            self.slider_opacity.setEnabled(False)
            for button in self.opacity_presets:
                button.setEnabled(False)
            self.label_opacity.setText("—")
            return
        entry = self.habillages[row]
        self.slider_opacity.blockSignals(True)
        self.slider_opacity.setValue(entry["opacity"])
        self.slider_opacity.blockSignals(False)
        self.slider_opacity.setEnabled(self._ready)
        for button in self.opacity_presets:
            button.setEnabled(self._ready)
        self.label_opacity.setText("{0} %".format(entry["opacity"]))

    def _on_opacity_changed(self, value):
        row = self.list_habillage.currentRow()
        if not 0 <= row < len(self.habillages):
            return
        entry = self.habillages[row]
        entry["opacity"] = value
        self.label_opacity.setText("{0} %".format(value))
        self._refresh_habillage_list()
        # Pas de nouveau rendu de couche : l'opacite ne s'applique qu'a la
        # composition, le calque rendu ne change pas.
        if entry["checked"] and not self.slider_opacity.isSliderDown():
            self._redraw()

    def _on_opacity_released(self):
        row = self.list_habillage.currentRow()
        if 0 <= row < len(self.habillages) and self.habillages[row]["checked"]:
            self._redraw()

    def _move_habillage(self, step):
        """Remonte ou descend l'habillage selectionne dans la pile."""
        row = self.list_habillage.currentRow()
        target = row + step
        if not (0 <= row < len(self.habillages)
                and 0 <= target < len(self.habillages)):
            return
        self.habillages[row], self.habillages[target] = (
            self.habillages[target], self.habillages[row]
        )
        self._refresh_habillage_list()
        self.list_habillage.setCurrentRow(target)
        if self.habillages[target]["checked"]:
            self._update_legend()
            self._redraw()

    def _set_status(self, text):
        self.label_status.setText(text)
        QApplication.processEvents()

    def _layers_for(self, key):
        """Couches QGIS d'un habillage, dans l'ordre d'empilement voulu.

        Un habillage peut en recouvrir plusieurs (l'agriculture, RPG et bio
        ensemble) - celles qui manquent pour ce bassin sont simplement
        omises plutot que de faire echouer tout l'habillage. Corine se
        telecharge a la demande, au premier appel seulement.
        """
        _key, layer_keys, _label = next(
            opt for opt in HABILLAGE_OPTIONS if opt[0] == key
        )
        if key == "corine":
            if self._corine_layer is None:
                from ..core import drape

                x = self.relief["x"]
                y = self.relief["y"]
                self._set_status(tr("view3d_habillage_loading", self.lang))
                bbox = (
                    float(min(x)), float(min(y)),
                    float(max(x)), float(max(y)),
                )
                self._corine_layer = drape.fetch_corine_layer(bbox)
                self._set_status("")
            return [self._corine_layer] if self._corine_layer else []
        if key == "ortho":
            if self._ortho_layer is None:
                from ..core import drape

                self._ortho_layer = drape.fetch_ortho_layer()
                if self._ortho_layer is None:
                    raise RuntimeError("Orthophoto IGN injoignable")
            return [self._ortho_layer]
        return [self.layers[lk] for lk in layer_keys if self.layers.get(lk)]

    def _render_habillage(self, key, factor=1):
        """Calque RVBA d'un habillage, rendu une fois puis garde en cache.

        factor > 1 le rend plus fin que la grille, pour la texture des
        exports 3D (voir export3d.fine_axes) ; chaque definition a sa propre
        entree de cache.

        Le relief gris n'est pas rendu par QGIS : il n'a pas de couche. Il
        n'est pas non plus un calque a composer - c'est le fond sur lequel les
        autres se posent - et _grey_base s'en charge. Il ne passe donc jamais
        par ici.
        """
        if key == RELIEF_GRIS:
            return None
        if (key, factor) in self._rendered:
            return self._rendered[(key, factor)]

        from ..core import drape

        layers = self._layers_for(key)
        x, y = self.relief["x"], self.relief["y"]
        if factor > 1:
            x, y = export3d.fine_axes(x, y, factor)
        image = drape.render_layer_texture(layers, x, y) if layers else None
        self._rendered[(key, factor)] = image
        return image

    def _grey_base(self, factor=1):
        """Fond uni qui deviendra le relief en niveaux de gris.

        Rien de plus qu'un aplat : c'est l'ombrage du bloc-diagramme
        (shade_rgb, dans charts) qui le sculpte ensuite avec les altitudes.
        Fabriquer ici un ombrage complet le ferait ombrer deux fois.
        """
        import numpy as np

        rows, cols = np.asarray(self.relief["grid"]).shape
        return np.full((rows * factor, cols * factor, 3), GREY_LEVEL,
                       dtype=np.uint8)

    def _current_texture(self, factor=1):
        """Image RVB composite des habillages coches, ou None si aucun.

        factor > 1 la compose plus fine que la grille, pour les exports 3D.

        Les calques sont poses du dessous vers le dessus, chacun avec son
        opacite. Sans habillage coche, la fonction rend None : le
        bloc-diagramme retrouve alors son nuancier hypsometrique, qui reste
        le meilleur rendu quand il n'y a rien a draper dessus.
        """
        import numpy as np

        from ..core import drape

        actifs = [e for e in self.habillages if e["checked"]]
        if not actifs:
            return None

        # self.habillages est range du dessus vers le dessous ; la
        # composition va dans l'autre sens.
        empiles = list(reversed(actifs))

        base = None
        if empiles and empiles[0]["key"] == RELIEF_GRIS:
            base = self._grey_base(factor)
            empiles = empiles[1:]
        if base is None:
            rows, cols = np.asarray(self.relief["grid"]).shape
            base = np.full((rows * factor, cols * factor, 3), 255,
                           dtype=np.uint8)

        calques = []
        for entry in empiles:
            if entry["key"] == RELIEF_GRIS:
                # Le relief gris remonte au-dessus d'un autre habillage : il
                # devient un voile uni, que son opacite rend utile ou non.
                grey = self._grey_base(factor)
                alpha = np.full(grey.shape[:2] + (1,), 255, dtype=np.uint8)
                calques.append(
                    (np.concatenate([grey, alpha], axis=2),
                     entry["opacity"] / 100.0)
                )
                continue
            image = self._render_habillage(entry["key"], factor)
            if image is not None:
                calques.append((image, entry["opacity"] / 100.0))
        return drape.flatten(base, calques)

    def _legend_entries(self):
        """(titre, [(couleur, libelle), ...]) des habillages actifs.

        La legende suit l'ordre de la pile : ce qui est dessus se lit en
        premier, comme dans le panneau des couches de QGIS. Partagee entre
        la colonne de legende et la page HTML exportee.
        """
        from ..core import drape

        entries = []
        for entry in self.habillages:
            if not entry["checked"] or entry["key"] == RELIEF_GRIS:
                continue   # le relief gris est un fond, il n'a pas de classes
            items = []
            for layer in self._layers_for(entry["key"]):
                items.extend(drape.legend_items(layer))
            if items:
                entries.append((tr(entry["label_key"], self.lang), items))
        return entries

    def _update_legend(self):
        """Reconstruit la legende a partir des habillages actifs."""
        while self.legend_layout.count() > 1:   # tout sauf le stretch final
            item = self.legend_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        has_content = False
        for title, items in self._legend_entries():
            has_content = True
            header = QLabel("<b>{0}</b>".format(title))
            self.legend_layout.insertWidget(
                self.legend_layout.count() - 1, header
            )
            for color, label in items:
                row = QHBoxLayout()
                swatch = QLabel()
                swatch.setFixedSize(12, 12)
                swatch.setStyleSheet(
                    "background-color:{0}; border:1px solid #888;".format(
                        color
                    )
                )
                row.addWidget(swatch)
                text = QLabel(str(label))
                text.setWordWrap(True)
                row.addWidget(text, 1)
                wrapper = QWidget()
                wrapper.setLayout(row)
                self.legend_layout.insertWidget(
                    self.legend_layout.count() - 1, wrapper
                )
        self.legend_panel.setVisible(has_content)

    def _redraw(self, view=None):
        if self.web is not None:
            self._refresh_web()
            return
        if self.axes is None or self.canvas is None or self.figure is None:
            return
        if view is None:
            view = self.axes.elev, self.axes.azim
        self.figure.clear()
        try:
            texture = self._current_texture()
        except Exception:
            texture = None
        self.axes = charts.relief_figure(
            self.relief, self.figure, texture=texture,
            **self._figure_options(view)
        )
        if self.axes is None:
            return
        self._tune_mouse()
        self._apply_zoom()   # redessine aussi le canevas

    def _export_image(self):
        """Sauve la vue courante en image, a la qualite et l'habillage affiches."""
        if not self._ready:
            return
        path, _filter = QFileDialog.getSaveFileName(
            self, tr("view3d_export", self.lang), "bloc_diagramme.png",
            "PNG (*.png)",
        )
        if not path:
            return
        if not path.lower().endswith(".png"):
            path += ".png"
        if self.web is not None:
            # Capture de la page telle qu'affichee, en-tete et boussole
            # compris - ce que l'on voit est ce que l'on enregistre.
            self.web.grab_image().save(path, "PNG")
        else:
            self.figure.savefig(path, dpi=charts.DPI, facecolor="white")
        self._set_status(tr("view3d_export_done", self.lang, path=path))

    def _fine_texture(self):
        """Texture fine des exports 3D, a l'habillage et l'eclairage affiches.

        Le chevelu, l'exutoire et la ligne de crete y sont peints selon les
        cases du groupe Affichage : l'export montre ce que montre l'apercu.
        """
        factor = export3d.texture_factor(self.relief)
        try:
            base = self._current_texture(factor)
        except Exception:
            base = None
        return export3d.fine_texture(
            self.relief, self.exaggeration, factor, base_rgb=base,
            light_azimuth=self.light_azimuth,
            light_altitude=self.light_altitude, cmap=self.palette,
            show_network=self.show_network, show_outlet=self.show_outlet,
            show_contour=self.show_contour,
        )

    def _run_export(self, title, default_name, file_filter, suffix, build):
        """Demande le fichier, construit le contenu, l'ecrit.

        build() renvoie des octets ou du texte, ou None si rien n'est
        exportable. Le curseur d'attente couvre la construction, qui prend
        quelques secondes sur un grand bassin (texture de 2 000 pixels).
        """
        path, _filter = QFileDialog.getSaveFileName(
            self, title, default_name, file_filter,
        )
        if not path:
            return None
        if not path.lower().endswith(suffix):
            path += suffix
        self._set_status(tr("view3d_export_working", self.lang))
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            content = build()
            if content is None:
                self._set_status(tr("view3d_missing", self.lang))
                return None
            if isinstance(content, str):
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write(content)
            else:
                with open(path, "wb") as handle:
                    handle.write(content)
        except Exception as exc:
            self._set_status(tr("done_error", self.lang, error=exc))
            return None
        finally:
            QApplication.restoreOverrideCursor()
        self._set_status(tr("view3d_export_done", self.lang, path=path))
        return path

    def _export_mesh(self):
        """Sauve le bloc-diagramme en maillage texture (.glb), pour Blender.

        A pleine resolution et a l'exageration, l'eclairage et l'habillage
        affiches : l'export reprend ce que montre l'apercu, plutot que de
        laisser l'outil qui rouvre le fichier deviner une echelle ou une
        couleur.
        """
        self._run_export(
            tr("view3d_export_mesh", self.lang), "bloc_diagramme.glb",
            "glTF binaire (*.glb)", ".glb",
            lambda: export3d.glb_bytes(
                self.relief, self.exaggeration, self._fine_texture()
            ),
        )

    def _export_html(self):
        """Sauve une page HTML autonome ou le bassin tourne a la souris.

        Un seul fichier, sans dependance ni reseau : de quoi l'envoyer a
        quelqu'un qui n'a pas QGIS.
        """
        path = self._run_export(
            tr("view3d_export_html", self.lang), "bassin_versant_3d.html",
            "HTML (*.html)", ".html",
            lambda: export3d.html_page(
                self.relief, self.exaggeration, None, self._html_texts(),
                interactive=self._interactive_data(),
            ),
        )
        if path:
            answer = QMessageBox.question(
                self, tr("view3d_export_html", self.lang),
                tr("view3d_html_open", self.lang, path=path),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if answer == QMessageBox.StandardButton.Yes:
                QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def _interactive_data(self):
        """Calques de la page HTML interactive : habillages, ombrage, traces.

        Tous les habillages disponibles partent dans la page, coches ou non,
        dans l'ordre, l'etat et l'opacite de la fenetre : la page les
        empile ensuite elle-meme. Un habillage qui ne se rend pas (service
        injoignable) est simplement omis plutot que de faire echouer
        l'export. Corine et l'orthophoto se telechargent donc ici s'ils ne
        l'ont pas encore ete - c'est ce qui fait durer l'export.
        """
        import numpy as np

        from ..core import drape

        factor = export3d.texture_factor(self.relief)
        rasters = export3d.relief_rasters(
            self.relief, self.exaggeration, factor,
            light_azimuth=self.light_azimuth,
            light_altitude=self.light_altitude, cmap=self.palette,
        )
        if rasters is None:
            return None
        hypso, shade = rasters

        layers = []
        for entry in self.habillages:
            rgba, legend = None, []
            if entry["key"] != RELIEF_GRIS:
                try:
                    rgba = self._render_habillage(entry["key"], factor)
                    for layer in self._layers_for(entry["key"]):
                        legend.extend(drape.legend_items(layer))
                except Exception:
                    rgba = None
                if rgba is None:
                    continue
            layers.append({
                "key": entry["key"], "label": tr(entry["label_key"], self.lang),
                "rgba": rgba, "checked": entry["checked"],
                "opacity": entry["opacity"], "legend": legend,
            })

        x = np.asarray(self.relief["x"], dtype=float)
        y = np.asarray(self.relief["y"], dtype=float)
        shape = hypso.shape[:2]
        overlays = [
            {"key": key, "label": label, "checked": checked,
             "rgba": export3d.overlay_rgba(self.relief, x, y, shape, key)}
            for key, label, checked in (
                ("reseau", tr("view3d_html_network", self.lang),
                 self.show_network),
                ("contour", tr("view3d_html_crest", self.lang),
                 self.show_contour),
                ("exutoire", tr("group_outlet", self.lang), self.show_outlet),
            )
        ]

        ui = {
            "view": tr("view3d_view_group", self.lang),
            "nw": tr("view3d_nw_short", self.lang),
            "top": tr("view3d_top_short", self.lang),
            "ne": tr("view3d_ne_short", self.lang),
            "sw": tr("view3d_sw_short", self.lang),
            "se": tr("view3d_se_short", self.lang),
            "zoomOut": tr("view3d_zoom_out", self.lang),
            "zoomIn": tr("view3d_zoom_in", self.lang),
            "layers": tr("view3d_habillage", self.lang),
            "up": tr("view3d_move_up", self.lang),
            "down": tr("view3d_move_down", self.lang),
            "opacity": tr("view3d_opacity", self.lang),
            "display": tr("view3d_html_display", self.lang),
            "exaggeration": tr("view3d_exaggeration", self.lang),
            "export": tr("view3d_export_group", self.lang),
            "png": tr("view3d_html_png", self.lang),
            "settings": tr("view3d_html_settings", self.lang),
            "legend": tr("view3d_legend_title", self.lang),
            "decimal": "." if self.lang == "en" else ",",
        }
        return export3d.interactive_data(
            hypso, shade, layers, overlays, GREY_LEVEL, ui)

    def _html_texts(self):
        """Libelles traduits de la page 3D, export et onglet web."""
        import numpy as np

        grid = np.asarray(self.relief["grid"], dtype=float)
        return {
            "title": tr("view3d_html_title", self.lang),
            "subtitle": tr(
                "view3d_html_subtitle", self.lang,
                low="{0:.0f}".format(float(np.nanmin(grid))),
                high="{0:.0f}".format(float(np.nanmax(grid))),
            ),
            "hint": tr("view3d_html_hint", self.lang),
            "reset": tr("view3d_html_reset", self.lang),
            "exaggeration": tr("view3d_exaggeration", self.lang),
            "nowebgl": tr("view3d_html_nowebgl", self.lang),
            "legend": tr("view3d_legend_title", self.lang),
        }
