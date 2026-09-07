# -*- coding: utf-8 -*-
"""Fenetre d'apercu du relief, tournante a la souris.

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
"""

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QApplication, QDialog, QFileDialog, QFrame, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton,
    QScrollArea, QSizePolicy, QSlider, QVBoxLayout, QWidget,
)

from ..i18n import tr
from ..report import charts

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

PANEL_WIDTH = 230
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
DEFINITION_DEFAULT = 1

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
# Le relief gris ferme la marche : c'est un fond, il n'a rien a masquer.
HABILLAGE_OPTIONS = (
    ("reseau", ("reseau",), "view3d_habillage_reseau"),
    ("agriculture", ("bio", "parcelles"), "view3d_habillage_agriculture"),
    ("foret", ("foret",), "view3d_habillage_foret"),
    ("corine", (), "view3d_habillage_corine"),
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
        # La vue par defaut est de biais (sud-ouest) : la ligne de partage
        # des eaux (voir relief_figure/show_contour) part donc masquee, comme
        # dans toutes les vues de biais - seul "Dessus" la fait apparaitre.
        self._view_mode = "oblique"
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
        self._rendered = {}           # cle -> calque RVBA rendu, mis en cache
        self._corine_layer = None     # telechargee une fois, gardee ensuite
        self.setWindowTitle(tr("btn_view3d", lang))
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )
        self.resize(1200, 760)

        self.axes = None
        self.figure = None
        self.canvas = None
        self._build_canvas_object()

        root = QHBoxLayout()
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        if self.canvas is None:
            root.addWidget(QLabel(tr("view3d_missing", lang)))
        else:
            self.legend_panel = self._build_legend_panel()
            self.legend_panel.setVisible(False)
            root.addWidget(self.legend_panel)

            viewport = QVBoxLayout()
            viewport.setSpacing(4)
            viewport.addWidget(self.canvas, 1)
            viewport.addWidget(QLabel(tr("view3d_hint", lang)))
            root.addLayout(viewport, 1)

            root.addWidget(self._build_panel())
        self.setLayout(root)

    # ------------------------------------------------------------- Montage

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
            self.relief, self.figure,
            exaggeration=self.exaggeration,
            decimate=self._current_decimate(),
            show_contour=(self._view_mode == "top"),
        )
        if self.axes is None:
            self.figure = None
            return
        self.canvas = FigureCanvasQTAgg(self.figure)

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
        """Panneau lateral : vue, habillage, export - un groupe par usage."""
        panel = QWidget()
        panel.setFixedWidth(PANEL_WIDTH)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        layout.addWidget(self._build_view_group())
        layout.addWidget(self._build_habillage_group())
        layout.addWidget(self._build_export_group())
        layout.addStretch(1)

        close = QPushButton(tr("close", self.lang))
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.setMinimumHeight(30)
        close.clicked.connect(self.accept)
        layout.addWidget(close)

        panel.setLayout(layout)
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
        self.btn_definition_minus = QPushButton(tr("view3d_zoom_out", self.lang))
        self.btn_definition_minus.clicked.connect(
            lambda: self._change_definition(-1)
        )
        self.label_definition = QLabel(
            "{0}/{1}".format(self.definition, DEFINITION_MAX)
        )
        self.label_definition.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_definition.setMinimumWidth(28)
        self.btn_definition_plus = QPushButton(tr("view3d_zoom_in", self.lang))
        self.btn_definition_plus.clicked.connect(
            lambda: self._change_definition(1)
        )
        for button in (self.btn_definition_minus, self.btn_definition_plus):
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setMinimumHeight(26)
        definition_row.addWidget(self.btn_definition_minus)
        definition_row.addWidget(self.label_definition)
        definition_row.addWidget(self.btn_definition_plus)

        column = QVBoxLayout()
        column.addLayout(grid)
        column.addLayout(zoom_row)
        column.addLayout(definition_row)
        group.setLayout(column)

        definition_buttons = (self.btn_definition_minus, self.btn_definition_plus)
        for button in (
            view_buttons + (self.btn_zoom_out, self.btn_zoom_in)
            + definition_buttons
        ):
            button.setEnabled(self.axes is not None)
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
        self.list_habillage.setEnabled(self.axes is not None)
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
            button.setEnabled(self.axes is not None)
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
        column.addWidget(self.slider_opacity)

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
        self.slider_exaggeration.setEnabled(self.axes is not None)
        self.slider_exaggeration.valueChanged.connect(
            self._on_exaggeration_changed
        )
        column.addWidget(self.slider_exaggeration)

        group.setLayout(column)
        return group

    def _build_export_group(self):
        group = QGroupBox(tr("view3d_export_group", self.lang))
        column = QVBoxLayout()

        self.btn_export_image = QPushButton(tr("view3d_export", self.lang))
        self.btn_export_image.clicked.connect(self._export_image)
        self.btn_export_mesh = QPushButton(tr("view3d_export_mesh", self.lang))
        self.btn_export_mesh.clicked.connect(self._export_mesh)
        for button in (self.btn_export_image, self.btn_export_mesh):
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setMinimumHeight(28)
            button.setEnabled(self.axes is not None)
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
        if self.axes is None or self.canvas is None:
            return
        self._view_mode = "top" if name == "top" else "oblique"
        self._redraw(view=VIEWS[name])

    def _zoom(self, factor):
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
        self._redraw()

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
            self.label_opacity.setText("—")
            return
        entry = self.habillages[row]
        self.slider_opacity.blockSignals(True)
        self.slider_opacity.setValue(entry["opacity"])
        self.slider_opacity.blockSignals(False)
        self.slider_opacity.setEnabled(self.axes is not None)
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
        if entry["checked"]:
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
        return [self.layers[lk] for lk in layer_keys if self.layers.get(lk)]

    def _render_habillage(self, key):
        """Calque RVBA d'un habillage, rendu une fois puis garde en cache.

        Le relief gris n'est pas rendu par QGIS : il n'a pas de couche. Il
        n'est pas non plus un calque a composer - c'est le fond sur lequel les
        autres se posent - et _grey_base s'en charge. Il ne passe donc jamais
        par ici.
        """
        if key == RELIEF_GRIS:
            return None
        if key in self._rendered:
            return self._rendered[key]

        from ..core import drape

        layers = self._layers_for(key)
        image = drape.render_layer_texture(
            layers, self.relief["x"], self.relief["y"]
        ) if layers else None
        self._rendered[key] = image
        return image

    def _grey_base(self):
        """Fond uni qui deviendra le relief en niveaux de gris.

        Rien de plus qu'un aplat : c'est l'ombrage du bloc-diagramme
        (shade_rgb, dans charts) qui le sculpte ensuite avec les altitudes.
        Fabriquer ici un ombrage complet le ferait ombrer deux fois.
        """
        import numpy as np

        shape = np.asarray(self.relief["grid"]).shape
        return np.full((shape[0], shape[1], 3), GREY_LEVEL, dtype=np.uint8)

    def _current_texture(self):
        """Image RVB composite des habillages coches, ou None si aucun.

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
            base = self._grey_base()
            empiles = empiles[1:]
        if base is None:
            shape = np.asarray(self.relief["grid"]).shape
            base = np.full((shape[0], shape[1], 3), 255, dtype=np.uint8)

        calques = []
        for entry in empiles:
            if entry["key"] == RELIEF_GRIS:
                # Le relief gris remonte au-dessus d'un autre habillage : il
                # devient un voile uni, que son opacite rend utile ou non.
                grey = self._grey_base()
                alpha = np.full(grey.shape[:2] + (1,), 255, dtype=np.uint8)
                calques.append(
                    (np.concatenate([grey, alpha], axis=2),
                     entry["opacity"] / 100.0)
                )
                continue
            image = self._render_habillage(entry["key"])
            if image is not None:
                calques.append((image, entry["opacity"] / 100.0))
        return drape.flatten(base, calques)

    def _update_legend(self):
        """Reconstruit la legende a partir des habillages actifs."""
        from ..core import drape

        while self.legend_layout.count() > 1:   # tout sauf le stretch final
            item = self.legend_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        has_content = False
        # La legende suit l'ordre de la pile : ce qui est dessus se lit en
        # premier, comme dans le panneau des couches de QGIS.
        for entry in self.habillages:
            if not entry["checked"] or entry["key"] == RELIEF_GRIS:
                continue   # le relief gris est un fond, il n'a pas de classes
            items = []
            for layer in self._layers_for(entry["key"]):
                items.extend(drape.legend_items(layer))
            if not items:
                continue
            has_content = True
            header = QLabel("<b>{0}</b>".format(
                tr(entry["label_key"], self.lang)))
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
        if self.axes is None or self.canvas is None or self.figure is None:
            return
        if view is None:
            view = self.axes.elev, self.axes.azim
        self.figure.clear()
        decimate = self._current_decimate()
        try:
            texture = self._current_texture()
        except Exception:
            texture = None
        self.axes = charts.relief_figure(
            self.relief, self.figure,
            elevation=view[0], azimuth=view[1],
            exaggeration=self.exaggeration, decimate=decimate,
            texture=texture, show_contour=(self._view_mode == "top"),
        )
        self._apply_zoom()   # redessine aussi le canevas

    def _export_image(self):
        """Sauve la vue courante en image, a la qualite et l'habillage affiches."""
        if self.figure is None:
            return
        path, _filter = QFileDialog.getSaveFileName(
            self, tr("view3d_export", self.lang), "bloc_diagramme.png",
            "PNG (*.png)",
        )
        if not path:
            return
        if not path.lower().endswith(".png"):
            path += ".png"
        self.figure.savefig(path, dpi=charts.DPI, facecolor="white")
        self._set_status(tr("view3d_export_done", self.lang, path=path))

    def _export_mesh(self):
        """Sauve le bloc-diagramme en maillage texture (.glb), pour Blender.

        A pleine resolution et a l'exageration et l'habillage affiches :
        l'export reprend exactement ce que montre l'apercu, plutot que de
        laisser l'outil qui rouvre le fichier deviner une echelle ou une
        couleur.
        """
        path, _filter = QFileDialog.getSaveFileName(
            self, tr("view3d_export_mesh", self.lang), "bloc_diagramme.glb",
            "glTF binaire (*.glb)",
        )
        if not path:
            return
        if not path.lower().endswith(".glb"):
            path += ".glb"
        try:
            texture = self._current_texture()
        except Exception:
            texture = None
        glb = charts.relief_mesh_glb(
            self.relief, exaggeration=self.exaggeration, decimate=1,
            texture=texture,
        )
        if glb is None:
            return
        with open(path, "wb") as handle:
            handle.write(glb)
        self._set_status(tr("view3d_export_done", self.lang, path=path))
