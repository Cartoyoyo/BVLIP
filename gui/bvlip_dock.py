# -*- coding: utf-8 -*-
"""Panneau lateral de BVLIP.

Le panneau ne contient aucune logique de traitement : il rassemble les
reglages, appelle core.pipeline et rend compte. La meme chaine est appelee par
l'algorithme Processing.

Le traitement part dans une tache de fond (voir bvlip_task). Le panneau ne
fait qu'emettre la demande et rendre compte : QGIS reste utilisable pendant
tout le calcul, qui peut durer plusieurs minutes sur un grand bassin.

Les couches ne sont fabriquees et ajoutees au projet qu'au retour de la tache,
donc dans le fil principal. Le fil de fond ne touche jamais au projet.

Rien n'est ecrit sur disque tant que l'utilisateur ne le demande pas. La
delimitation produit des couches en memoire ; le rapport ne s'ecrit que par le
bouton dedie, qui demande alors ou l'enregistrer.

Le panneau ne porte que le geste courant : choisir un exutoire, lancer,
suivre. Tout ce qu'on regle une fois et qu'on ne retouche plus - accrochage,
etapes facultatives, langue, fiche du plugin - vit dans le menu de
l'extension. Un panneau qui tient dans un coin d'ecran reste utilisable a
cote d'une carte ; un panneau qui affiche tous les reglages ne l'est plus.
"""

import os
import time

from qgis.core import Qgis
from qgis.PyQt import sip
from qgis.PyQt.QtCore import QPoint, Qt, QTimer, QUrl
from qgis.PyQt.QtGui import QDesktopServices, QFont
from qgis.PyQt.QtWidgets import (
    QApplication, QCheckBox, QDockWidget, QFileDialog, QFrame, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QMessageBox, QProgressBar, QPushButton,
    QScrollArea, QSizePolicy, QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)

from ..core import datasets as catalogue
from ..core.network import SEED_FEATURE_MAX, OversizeBasinError
from ..i18n import tr
from . import settings
from .outlet_map_tool import OutletMapTool

# Hauteur commune a tous les boutons du panneau.
BTN_HEIGHT = 30

# Hauteur en deca de laquelle on ne retrecit jamais le panneau, meme si
# l'ecran est minuscule : en dessous, l'ascenseur aurait plus de course que de
# fenetre et le panneau cesserait d'etre utilisable.
PANEL_MIN_HEIGHT = 240

# Marge gardee sous le panneau, pour que sa bordure reste attrapable.
PANEL_BOTTOM_MARGIN = 4

# Hauteur du bloc des onglets de donnees, la meme pour les quatre.
#
# Elle avait d'abord ete calculee par onglet, pour qu'aucun ne garde de vide
# sous ses cases. Mal lui en a pris : le cadre qui l'entoure ne se
# redimensionne pas au meme moment, et les cases venaient se poser sur les
# boutons de selection. Une hauteur unique ne coute qu'un peu de vide sur les
# onglets courts, et elle ne se decale jamais.
#
# Huit lignes visibles sur les douze zonages : assez pour que la barre de
# defilement se voie et dise qu'il y en a d'autres.
TAB_HEIGHT = 212

BTN_PRIMARY = (
    "QPushButton{background:#2c3e50;color:#fff;border-radius:5px;"
    "font-weight:bold;font-size:11px}"
    "QPushButton:hover{background:#3d5166}"
    "QPushButton:disabled{background:#95a5a6}"
)
BTN_REPORT = (
    "QPushButton{background:#8e44ad;color:#fff;border-radius:5px;"
    "font-weight:bold;font-size:11px}"
    "QPushButton:hover{background:#9b59b6}"
    "QPushButton:disabled{background:#bdc3c7}"
)
BTN_PICK = (
    "QPushButton{background:#16a085;color:#fff;border-radius:5px;"
    "font-weight:bold;font-size:11px}"
    "QPushButton:hover{background:#1abc9c}"
    "QPushButton:checked{background:#c0392b}"
    "QPushButton:disabled{background:#95a5a6}"
)
# Le fond de plan ne lance rien non plus : meme famille que les boutons de
# selection.
BTN_BASEMAP = (
    "QPushButton{background:#ecf0f1;color:#2c3e50;border:1px solid #bdc3c7;"
    "border-radius:4px;font-size:11px;padding:2px 8px}"
    "QPushButton:hover{background:#dfe4e6}"
)
# Les deux boutons de selection ne lancent rien : ils se presentent donc en
# retrait, comme les liens d'une barre d'outils et non comme des actions.
BTN_SMALL = (
    "QPushButton{background:#ecf0f1;color:#2c3e50;border:1px solid #bdc3c7;"
    "border-radius:4px;font-size:11px;padding:2px 10px}"
    "QPushButton:hover{background:#dfe4e6}"
    "QPushButton:disabled{color:#95a5a6}"
)
# Le i des descriptions : present sans peser, il ne doit pas concurrencer du
# regard la case qu'il accompagne.
INFO_MARK = "QLabel{color:#7f8c8d;font-size:12px}QLabel:hover{color:#2980b9}"
BTN_CANCEL = (
    "QPushButton{background:#c0392b;color:#fff;border-radius:5px;"
    "font-weight:bold;font-size:11px}"
    "QPushButton:hover{background:#d44534}"
    "QPushButton:disabled{background:#bdc3c7}"
)
# L'apercu est le cadet du rapport : meme famille de couleur, ton plus clair.
# Il n'ecrit rien, il n'a donc pas a se presenter avec le meme poids que le
# bouton qui, lui, produit des fichiers.
BTN_PREVIEW = (
    "QPushButton{background:#a569bd;color:#fff;border-radius:5px;"
    "font-weight:bold;font-size:11px}"
    "QPushButton:hover{background:#b784cd}"
    "QPushButton:disabled{background:#bdc3c7}"
)
# La vue en relief n'ecrit rien elle non plus, mais elle ne produit pas la
# meme chose que le rapport : elle sort de sa famille de couleur.
BTN_VIEW3D = (
    "QPushButton{background:#2e86c1;color:#fff;border-radius:5px;"
    "font-weight:bold;font-size:11px}"
    "QPushButton:hover{background:#3f96d1}"
    "QPushButton:disabled{background:#bdc3c7}"
)

class BvlipDock(QDockWidget):
    """Panneau principal : choix de l'exutoire, options, execution, journal."""

    def __init__(self, iface, lang, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.lang = lang
        self.outlet = None       # (x, y) en Lambert 93
        self.last_result = None  # dernier resultat du pipeline
        self.last_click = None
        self.last_layers = None
        self._running = False    # un traitement est-il en cours ?
        self._task = None        # tache de fond en cours, le cas echeant
        self._started = 0.0
        self._click_of_run = None
        # Demande de calcul integral : posee par la boite de dialogue
        # du bassin hors gabarit, consommee par le lancement suivant
        # et jamais conservee. Un exutoire different repart du
        # garde-fou : l'accord donne une fois ne vaut pas pour la
        # suite.
        self._allow_oversize = False
        # Chevelu deja charge par un calcul refuse, a poursuivre. Il est lie
        # a un exutoire : changer de point l'invalide.
        self._resume = None

        self.map_tool = OutletMapTool(self.canvas)
        self.map_tool.outlet_picked.connect(self._on_outlet_picked)
        self.map_tool.deactivated.connect(self._on_tool_deactivated)

        self.setObjectName("BvlipDock")
        self._build_ui()
        self.retranslate()

        # Le panneau se reborne des qu'il bouge : change de bord, se detache,
        # ou change d'ecran. Sa hauteur utile depend de l'endroit ou il est
        # pose, pas seulement de sa taille.
        self.dockLocationChanged.connect(lambda _area: self._limit_to_screen())
        self.topLevelChanged.connect(lambda _floating: self._limit_to_screen())

    # ------------------------------------------------------------------ UI

    def _build_ui(self):
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Exutoire
        self.grp_outlet = QGroupBox()
        outlet_layout = QVBoxLayout()
        pick_row = QHBoxLayout()
        pick_row.setSpacing(6)
        self.btn_pick = QPushButton()
        self.btn_pick.setCheckable(True)
        self.btn_pick.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pick.setStyleSheet(BTN_PICK)
        self.btn_pick.clicked.connect(self._on_pick_toggled)
        pick_row.addWidget(self.btn_pick, 1)

        # Fond de plan facultatif : un raccourci, pas une action liee au
        # calcul. Il vit donc a cote du bouton de pointage plutot que dans
        # la pile des boutons d'execution, avec le meme poids dans la ligne.
        self.btn_basemap = QPushButton()
        self.btn_basemap.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_basemap.setStyleSheet(BTN_BASEMAP)
        self.btn_basemap.clicked.connect(self._add_opentopomap)
        pick_row.addWidget(self.btn_basemap, 1)
        outlet_layout.addLayout(pick_row)

        self.lbl_outlet = QLabel()
        font_outlet = QFont()
        font_outlet.setBold(True)
        self.lbl_outlet.setFont(font_outlet)
        self.lbl_outlet.setStyleSheet("color:#c0392b")
        outlet_layout.addWidget(self.lbl_outlet)

        self.grp_outlet.setLayout(outlet_layout)
        layout.addWidget(self.grp_outlet)

        # Ce qu'on rapatrie se decide d'un bassin a l'autre : la liste reste
        # donc sous la main, dans le panneau. Les reglages d'accrochage, eux,
        # se posent une fois et vivent dans le menu de l'extension.
        #
        # Une case par donnee, rangees en onglets. Vingt-deux cases a la
        # suite feraient un panneau qu'on parcourt a la molette et ou l'on ne
        # trouve rien ; reparties en quatre familles, chacune se lit d'un
        # coup et l'onglet dit deja de quoi il retourne. Les zonages sont a
        # eux seuls la moitie de la liste, ce qui justifiait de les isoler.
        self.grp_options = QGroupBox()
        options_layout = QVBoxLayout()
        options_layout.setSpacing(6)
        chosen = settings.selected_datasets()

        self.tabs_options = QTabWidget()
        self.tabs_options.setFixedHeight(TAB_HEIGHT)
        self.chk_datasets = {}
        self.info_datasets = {}
        for tab in catalogue.TABS:
            page = QWidget()
            page_layout = QVBoxLayout()
            page_layout.setContentsMargins(8, 8, 8, 4)
            page_layout.setSpacing(4)
            for key in catalogue.keys_of(tab):
                # Une case, puis un i discret cale a droite. La description
                # complete ne peut pas tenir dans l'intitule - il en faudrait
                # quatre lignes - et elle ne peut pas non plus etre passee
                # sous silence : ce que rapatrie une case, et surtout la
                # reserve qui l'accompagne, ne se devinent pas de son nom.
                row = QHBoxLayout()
                row.setSpacing(4)
                box = QCheckBox()
                box.setChecked(key in chosen)
                box.toggled.connect(self._save_options)
                self.chk_datasets[key] = box
                row.addWidget(box, 1)

                info = QLabel("ⓘ")
                info.setStyleSheet(INFO_MARK)
                info.setCursor(Qt.CursorShape.WhatsThisCursor)
                self.info_datasets[key] = info
                row.addWidget(info, 0)
                page_layout.addLayout(row)
            page_layout.addStretch()
            page.setLayout(page_layout)

            scroll = QScrollArea()
            scroll.setWidget(page)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            self.tabs_options.addTab(scroll, "")
        options_layout.addWidget(self.tabs_options)

        # Tout cocher ou tout decocher porte sur l'onglet affiche, pas sur la
        # liste entiere : c'est le geste dont on a besoin sur les douze
        # zonages, et l'appliquer aux vingt-deux cases effacerait un choix
        # fait dans un autre onglet sans que rien ne le montre.
        select_row = QHBoxLayout()
        select_row.setSpacing(6)
        self.btn_all = QPushButton()
        self.btn_all.setStyleSheet(BTN_SMALL)
        self.btn_all.clicked.connect(lambda: self._set_current_tab(True))
        self.btn_none = QPushButton()
        self.btn_none.setStyleSheet(BTN_SMALL)
        self.btn_none.clicked.connect(lambda: self._set_current_tab(False))
        select_row.addWidget(self.btn_all)
        select_row.addWidget(self.btn_none)
        select_row.addStretch()
        self.lbl_datasets = QLabel()
        self.lbl_datasets.setStyleSheet("color:#7f8c8d;font-size:11px")
        select_row.addWidget(self.lbl_datasets)
        options_layout.addLayout(select_row)

        self.grp_options.setLayout(options_layout)
        layout.addWidget(self.grp_options)

        # Execution. Une grille a deux colonnes de meme poids, et non une
        # boite horizontale : celle-ci ne repartit que l'espace *supplementaire*
        # et laisse au bouton au texte le plus long une largeur plus grande.
        run_row = QGridLayout()
        run_row.setSpacing(6)
        run_row.setColumnStretch(0, 1)
        run_row.setColumnStretch(1, 1)
        self.btn_run = QPushButton()
        self.btn_run.setStyleSheet(BTN_PRIMARY)
        self.btn_run.clicked.connect(self.run)
        run_row.addWidget(self.btn_run, 0, 0)

        # Le calcul tournant en fond, il devient possible de l'interrompre :
        # le bouton n'a de sens que depuis que l'interface reste vivante.
        self.btn_cancel = QPushButton()
        self.btn_cancel.setStyleSheet(BTN_CANCEL)
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.cancel)
        run_row.addWidget(self.btn_cancel, 0, 1)
        layout.addLayout(run_row)

        # Le rapport est une demande separee : il s'ecrit sur disque, donc il
        # ne part jamais tout seul a la suite d'un calcul.
        self.btn_report = QPushButton()
        self.btn_report.setStyleSheet(BTN_REPORT)
        self.btn_report.setEnabled(False)
        self.btn_report.clicked.connect(self.make_report)
        layout.addWidget(self.btn_report)

        # L'apercu vient apres le rapport dans la pile, mais avant lui dans
        # l'usage : on regarde la page, puis on decide de l'enregistrer.
        self.btn_preview = QPushButton()
        self.btn_preview.setStyleSheet(BTN_PREVIEW)
        self.btn_preview.setEnabled(False)
        self.btn_preview.clicked.connect(self.show_preview)
        layout.addWidget(self.btn_preview)

        self.btn_view3d = QPushButton()
        self.btn_view3d.setStyleSheet(BTN_VIEW3D)
        self.btn_view3d.setEnabled(False)
        self.btn_view3d.clicked.connect(self.show_view3d)
        layout.addWidget(self.btn_view3d)

        # Tous les boutons a la meme hauteur, et les deux boutons cote a cote
        # a la meme largeur : c'est la regularite qui rend une pile de boutons
        # lisible, pas la taille de chacun.
        for button in (self.btn_pick, self.btn_basemap, self.btn_run,
                       self.btn_cancel, self.btn_report, self.btn_preview,
                       self.btn_view3d):
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setMinimumHeight(BTN_HEIGHT)
            button.setMaximumHeight(BTN_HEIGHT)
            policy = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
            button.setSizePolicy(policy)

        self.lbl_status = QLabel()
        self.lbl_status.setWordWrap(True)
        layout.addWidget(self.lbl_status)
        self.progress = QProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFixedHeight(150)
        # Chasse fixe : les horodatages ne forment une colonne lisible que si
        # tous les chiffres ont la meme largeur. Avec une police
        # proportionnelle, la colonne ondule et l'oeil ne peut plus comparer
        # deux lignes d'un coup.
        mono = QFont(self.log_area.font())
        mono.setFamilies(["Consolas", "DejaVu Sans Mono", "Courier New",
                          "monospace"])
        mono.setFixedPitch(True)
        self.log_area.setFont(mono)
        layout.addWidget(self.log_area)

        layout.addStretch()
        container.setLayout(layout)

        # Le panneau entier defile. Empile, son contenu demande environ sept
        # cents pixels de haut : l'exutoire, les quatre onglets de donnees,
        # cinq boutons, la barre d'avancement et le journal. Sur un portable,
        # ou le bandeau lateral en offre quatre cents, le bas etait tout
        # bonnement hors d'atteinte - le bouton de rapport comme le journal -
        # sans que rien ne signale qu'il existait.
        #
        # L'ascenseur horizontal est laisse au besoin plutot qu'interdit : un
        # panneau retreci sous la largeur de la barre d'onglets doit se
        # parcourir, pas se faire couper.
        scroll = QScrollArea()
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll = scroll
        self.setWidget(scroll)

    # ------------------------------------------------- Tenue a l'ecran

    def _limit_to_screen(self):
        """Empeche le panneau de descendre sous le bas visible de l'ecran.

        L'ascenseur ne se declenche que si Qt voit un debordement, et Qt ne
        regarde que le dock : tant que le contenu tient dedans, pas de barre.
        Or le dock, lui, peut deborder de l'ecran sans que Qt s'en emeuve.

        Releve sur un poste : ecran 1366 x 768, fenetre QGIS maximisee a
        1368 x 1023 - trois cents pixels de plus que l'ecran, un reste de
        geometrie d'un autre moniteur que Windows conserve. Le panneau ancre
        a droite y faisait 789 pixels de haut, dont 267 sous le bord bas de
        l'ecran. Son contenu tenait tout juste dans ses 770 pixels : aucun
        ascenseur, et un quart du panneau inatteignable, journal compris.

        On borne donc le panneau a ce que l'ecran montre vraiment. Le reste
        du dock, s'il en subsiste, est hors champ de toute facon, et
        l'ascenseur reprend son office.
        """
        if not self._alive(self):
            return
        screen = self.screen() if hasattr(self, "screen") else None
        if screen is None:
            return
        area = screen.availableGeometry()

        # Detache, le panneau est une fenetre a lui seul : on peut la remonter
        # dans l'ecran au lieu de se contenter de la raccourcir. Ancre, sa
        # position est celle que lui donne la fenetre principale, et seule sa
        # hauteur nous appartient.
        if self.isFloating():
            frame = self.frameGeometry()
            if frame.bottom() > area.bottom() or frame.top() < area.top():
                self.move(frame.x(),
                          max(area.top(),
                              min(frame.y(),
                                  area.bottom() - frame.height())))

        top = self.mapToGlobal(QPoint(0, 0)).y()
        room = max(PANEL_MIN_HEIGHT, area.bottom() - top - PANEL_BOTTOM_MARGIN)
        # Seule une valeur qui change est posee : setMaximumHeight declenche
        # un redimensionnement, qui rappellerait cette methode.
        if self.maximumHeight() != room:
            self.setMaximumHeight(room)

    def showEvent(self, event):          # noqa: N802 (API Qt)
        super().showEvent(event)
        # Au premier affichage, la position du panneau n'est connue qu'une
        # fois la fenetre posee : on repasse donc apres la boucle d'evenements.
        QTimer.singleShot(0, self._limit_to_screen)

    def resizeEvent(self, event):        # noqa: N802 (API Qt)
        super().resizeEvent(event)
        self._limit_to_screen()

    def moveEvent(self, event):          # noqa: N802 (API Qt)
        super().moveEvent(event)
        self._limit_to_screen()

    def retranslate(self):
        """Reapplique tous les libelles dans la langue courante."""
        lang = self.lang
        self.setWindowTitle(tr("plugin_title", lang))
        self.grp_outlet.setTitle(tr("group_outlet", lang))
        self.btn_pick.setText(tr("btn_pick", lang))
        self.btn_basemap.setText(tr("btn_opentopomap", lang))
        self.btn_basemap.setToolTip(tr("opentopomap_tip", lang))
        self.grp_options.setTitle(tr("group_options", lang))
        for index, tab in enumerate(catalogue.TABS):
            self.tabs_options.setTabText(
                index, tr(catalogue.tab_label_key(tab), lang))
        for key, box in self.chk_datasets.items():
            box.setText(tr(catalogue.label_key(key), lang))
            # La meme description sur la case et sur son i : le survol de
            # l'un ou de l'autre doit apprendre la meme chose, le i n'etant
            # qu'un reperage visuel.
            description = tr(catalogue.info_key(key), lang)
            box.setToolTip(description)
            self.info_datasets[key].setToolTip(description)
        self.btn_all.setText(tr("btn_select_all", lang))
        self.btn_none.setText(tr("btn_select_none", lang))
        self._refresh_dataset_count()
        self.btn_run.setText(tr("btn_run", lang))
        self.btn_cancel.setText(tr("btn_cancel", lang))
        self.btn_report.setText(tr("btn_report", lang))
        self.btn_report.setToolTip(tr("report_tip", lang))
        self.btn_preview.setText(tr("btn_preview", lang))
        self.btn_preview.setToolTip(tr("preview_tip", lang))
        self.btn_view3d.setText(tr("btn_view3d", lang))
        self.btn_view3d.setToolTip(tr("view3d_tip", lang))
        self.lbl_status.setText(tr("ready", lang))
        self.progress.setFormat(tr("progress_fmt", lang))
        self._refresh_outlet_label()

    # --------------------------------------------------------------- Slots

    def _selected_datasets(self):
        return {key for key, box in self.chk_datasets.items()
                if box.isChecked()}

    def _save_options(self, _checked=False):
        """Les cases sont la source de verite : elles s'enregistrent aussitot.

        Le traitement relit les reglages au lancement, il n'y a donc qu'un
        seul endroit ou l'etat est conserve.
        """
        settings.save_datasets(self._selected_datasets())
        self._refresh_dataset_count()

    def _refresh_dataset_count(self):
        """Rappelle combien de donnees sont cochees, tous onglets confondus.

        Sans ce compte, un onglet replie peut cacher une case decochee et le
        rapport arriverait ampute sans que rien ne l'ait annonce.
        """
        if not self._alive(self.lbl_datasets):
            return
        self.lbl_datasets.setText(tr("datasets_count", self.lang).format(
            len(self._selected_datasets()), len(catalogue.KEYS)))

    def _set_current_tab(self, checked):
        """Coche ou decoche toutes les cases de l'onglet affiche."""
        index = self.tabs_options.currentIndex()
        if not 0 <= index < len(catalogue.TABS):
            return
        for key in catalogue.keys_of(catalogue.TABS[index]):
            box = self.chk_datasets.get(key)
            if box is not None and self._alive(box):
                # blockSignals evite d'ecrire les reglages une fois par case :
                # l'enregistrement se fait une seule fois, a la fin.
                box.blockSignals(True)
                box.setChecked(checked)
                box.blockSignals(False)
        self._save_options()

    def _add_opentopomap(self):
        """Ajoute le fond de plan OpenTopoMap au projet, en couche XYZ.

        Un simple raccourci de confort : le releve du relief sous les yeux
        aide a poser l'exutoire au bon endroit, sans passer par le
        gestionnaire de connexions XYZ de QGIS.
        """
        from qgis.core import QgsProject, QgsRasterLayer

        from ..core.results import CRS

        name = "OpenTopoMap"
        project = QgsProject.instance()
        for layer in project.mapLayers().values():
            if layer.name() == name:
                self._status(tr("opentopomap_added", self.lang))
                return

        url = ("type=xyz&url=https://a.tile.opentopomap.org/"
               "%7Bz%7D/%7Bx%7D/%7By%7D.png&zmax=17&zmin=0")
        layer = QgsRasterLayer(url, name, "wms")
        if not layer.isValid():
            self.log(tr("done_error", self.lang,
                        error="OpenTopoMap: " + layer.error().message()))
            return

        # La tuile XYZ n'existe qu'en Web Mercator : sur un projet dont le
        # CRS n'a encore jamais ete choisi, QGIS adopte la projection de la
        # premiere couche ajoutee, le canevas bascule en EPSG:3857, et le
        # cadrage sur le bassin en fin de calcul (toujours produit en
        # Lambert 93) atterrit hors champ. Le CRS d'avant l'ajout est donc
        # garde : s'il etait deja valide - Lambert 93 ou un autre, choisi par
        # le projet lui-meme - on le restaure tel quel apres coup ; s'il n'y
        # en avait pas encore, 2154 devient le choix par defaut.
        crs_before = project.crs()
        project.addMapLayer(layer)
        if crs_before.isValid():
            project.setCrs(crs_before)
        else:
            project.setCrs(CRS)
        self._status(tr("opentopomap_added", self.lang))
        self.log(tr("opentopomap_added", self.lang))

    def _on_pick_toggled(self, checked):
        if checked:
            self.canvas.setMapTool(self.map_tool)
        else:
            self.canvas.unsetMapTool(self.map_tool)

    def _on_tool_deactivated(self):
        self.btn_pick.setChecked(False)

    def _on_outlet_picked(self, x, y):
        # Un autre exutoire invalide ce qui avait ete charge pour le
        # precedent : le chevelu amont n'est pas le meme.
        self._resume = None
        self._allow_oversize = False
        self.outlet = (x, y)
        self._refresh_outlet_label()
        self.btn_pick.setChecked(False)
        self.canvas.unsetMapTool(self.map_tool)

    def _refresh_outlet_label(self):
        if self.outlet is None:
            self.lbl_outlet.setText(tr("no_outlet", self.lang))
            self.lbl_outlet.setStyleSheet("color:#c0392b")
        else:
            self.lbl_outlet.setText(
                tr("outlet_set", self.lang, x=self.outlet[0], y=self.outlet[1])
            )
            self.lbl_outlet.setStyleSheet("color:#16a085")

    # ----------------------------------------------------------- Execution

    @staticmethod
    def _alive(widget):
        """Le widget existe-t-il encore du cote de Qt ?

        processEvents rend la main a Qt au milieu du traitement : le panneau
        peut donc etre ferme, ou le plugin recharge, alors que la chaine
        tourne encore. L'objet Python survit a son homologue C++, et toute
        methode appelee ensuite leve une RuntimeError. On verifie donc avant
        de toucher a l'interface, plutot que de laisser une pile d'erreurs
        s'empiler jusqu'au bloc finally.
        """
        try:
            return widget is not None and not sip.isdeleted(widget)
        except (RuntimeError, TypeError):
            return False

    def _status(self, text):
        """Pose le statut, ramene a sa premiere ligne.

        L'etiquette tient sur deux ou trois lignes dans un panneau etroit :
        un message multi-ligne la fait grandir jusqu'a chasser le journal
        hors de l'ecran. Le detail, lui, reste dans le journal juste dessous.
        """
        if not self._alive(self.lbl_status):
            return
        lines = str(text).strip().splitlines()
        self.lbl_status.setText(lines[0] if lines else str(text))

    def _stamp(self):
        """Prefixe horodate d'une ligne de journal.

        L'heure dit quand l'etape a eu lieu, le compteur depuis combien de
        temps le calcul tourne. C'est le second qui sert le plus : l'ecart
        entre deux lignes montre d'un coup d'oeil ou le temps est passe, sans
        avoir a soustraire des heures de tete.
        """
        clock = time.strftime("%H:%M:%S")
        if self._started:
            return "{0} {1:5.0f}s  ".format(clock, time.time() - self._started)
        return "{0}          ".format(clock)

    def log(self, message):
        if not self._alive(self.log_area):
            return
        # Chaque ligne du message porte son propre horodatage : un resume qui
        # tient sur six lignes ne doit pas paraitre instantane sur cinq
        # d'entre elles.
        stamp = self._stamp()
        for line in str(message).splitlines() or [""]:
            self.log_area.append(stamp + line)
        QApplication.processEvents()

    def set_controls_enabled(self, enabled):
        for widget in (self.btn_run, self.btn_pick, self.tabs_options,
                       self.btn_all, self.btn_none):
            if self._alive(widget):
                widget.setEnabled(enabled)
        for button in (self.btn_report, self.btn_preview,
                       self.btn_view3d):
            # Les deux sortent la meme page : ils s'allument ensemble, des
            # qu'un bassin est calcule, et s'eteignent pendant un traitement.
            if self._alive(button):
                button.setEnabled(enabled and self.last_result is not None)
        if self._alive(self.btn_cancel):
            self.btn_cancel.setEnabled(not enabled and self._task is not None)

    def run(self):
        """Lance la delimitation dans une tache de fond.

        Le panneau n'attend pas : il rend la main aussitot et se contente de
        rendre compte quand la tache le lui signale. QGIS reste utilisable
        pendant tout le calcul, qui peut durer plusieurs minutes sur un grand
        bassin.
        """
        from qgis.core import QgsApplication
        from ..core.pipeline import STEPS
        from . import settings
        from .bvlip_task import BvlipTask

        # Le bouton est verrouille pendant le traitement, mais un second
        # declenchement peut venir d'ailleurs : raccourci, appel programme.
        if self._running:
            return

        # Le journal n'est efface qu'au demarrage d'un calcul neuf. Sur une
        # reprise, il porte tout ce qui a deja ete parcouru : l'effacer
        # donnerait l'impression de repartir de zero alors que le chevelu
        # deja charge est conserve.
        resume = self._resume
        if resume is None:
            self.log_area.clear()
        if self.outlet is None:
            self.log(tr("err_no_outlet", self.lang))
            return

        # Les reglages viennent du menu de l'extension, pas du panneau : ils
        # sont relus a chaque lancement, donc une modification prend effet
        # sans rouvrir le panneau.
        options = settings.pipeline_options(
            allow_oversize=self._allow_oversize
        )
        # L'accord de calcul integral et le chevelu deja charge se consomment
        # ici : ils valent pour ce lancement et pour lui seul. La reprise a
        # ete recuperee plus haut, avant l'effacement du journal.
        self._allow_oversize = False
        self._resume = None

        self.last_result = None
        self._running = True
        self._started = time.time()
        self._click_of_run = self.outlet
        self.progress.setMaximum(len(STEPS))
        self.progress.setValue(0)
        if resume is None:
            self.log(tr("outlet_set", self.lang,
                        x=self.outlet[0], y=self.outlet[1]))
        else:
            self.log(tr("resuming", self.lang,
                        dalles=len(resume.get("loaded") or ()),
                        troncons=len(resume.get("network") or ())))
        self.log(tr("running_background", self.lang))

        task = BvlipTask(self.outlet[0], self.outlet[1], options,
                         resume=resume)
        task.set_step_count(len(STEPS))
        task.step.connect(self._on_step)
        task.finished_with.connect(self._on_finished)
        # La reference est conservee : sans elle, l'objet Python serait
        # recupere par le ramasse-miettes alors que la tache tourne encore.
        # Elle est posee avant le verrouillage des controles, dont depend
        # l'activation du bouton Annuler.
        self._task = task
        self.set_controls_enabled(False)
        QgsApplication.taskManager().addTask(task)

    def cancel(self):
        """Demande l'arret de la tache en cours."""
        if self._task is not None:
            self._task.cancel()

    def _on_finished(self, result, error):
        """Retour de la tache, dans le fil principal.

        C'est ici, et seulement ici, que les couches sont fabriquees et
        ajoutees au projet : le fil de fond ne touche jamais au projet.
        """
        from ..core import results
        from ..core.pipeline import STEPS, summary

        self._task = None
        self._running = False
        try:
            if isinstance(error, OversizeBasinError):
                self._ask_oversize(error)
                return
            if error:
                self.log(tr("done_error", self.lang, error=error))
                self._status(tr("done_error", self.lang, error=error))
                return
            if result is None:
                self.log(tr("cancelled", self.lang))
                self._status(tr("cancelled", self.lang))
                if self._alive(self.progress):
                    self.progress.setValue(0)
                return

            for warning in result["avertissements"]:
                self.log(tr("warning", self.lang, message=warning))

            layers, _basin_id, groups = results.build_layers(
                result, self._click_of_run
            )
            # Un nom parlant par resultat : deux bassins calcules a la suite
            # ne se retrouvent plus sous deux groupes homonymes.
            group = results.add_to_project(
                layers, group_name=results.group_label(groups),
                iface=self.iface,
            )

            self.last_result = result
            self.last_click = self._click_of_run
            self.last_layers = layers

            if self._alive(self.progress):
                self.progress.setValue(len(STEPS))
            self.log(tr("layers_added", self.lang, group=group.name()))
            self.log(summary(result))
            self._status(tr("done_ok", self.lang,
                            seconds=time.time() - self._started))
        except Exception as exc:
            self.log(tr("done_error", self.lang, error=exc))
            self._status(tr("done_error", self.lang, error=exc))
        finally:
            self.set_controls_enabled(True)
            # Le chrono s'arrete ici, et pas a l'entree de cette methode :
            # les couches et le resume sont produits entre-temps, et ce
            # travail-la fait partie du calcul.
            self._started = 0.0

    def _on_step(self, index, message):
        """Retour d'avancement de la chaine de traitement."""
        from ..core.pipeline import STEPS
        if self._alive(self.progress):
            self.progress.setValue(index)
        self._status(tr(
            "step_running", self.lang, step=index + 1, total=len(STEPS),
            label=message,
        ))
        self.log("  " + str(message))

    def _ask_oversize(self, error):
        """Bassin hors gabarit : annoncer, puis laisser le choix.

        Le calcul s'est arrete parce que le bassin deborde du garde-fou, pas
        parce qu'il aurait echoue. La difference compte : il n'y a rien a
        reparer, il y a une decision a prendre, et elle n'appartient pas au
        plugin. On montre donc ce qui a ete atteint, ce que couterait la
        suite, et on laisse la main.

        Le refus est le choix par defaut. Dans la grande majorite des cas,
        un bassin qui deborde a 60 km signale un exutoire pose sur un fleuve
        par megarde, et non une intention.
        """
        self.log(tr("oversize_log", self.lang,
                    count=error.feature_count,
                    budget=error.budget,
                    upstream=error.upstream_count,
                    lineaire_km=error.upstream_km))
        self._status(tr("oversize_status", self.lang))
        if self._alive(self.progress):
            self.progress.setValue(0)

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle(tr("oversize_title", self.lang))
        box.setText(tr("oversize_text", self.lang,
                       count=error.feature_count, budget=error.budget))
        box.setInformativeText(tr(
            "oversize_detail", self.lang,
            upstream=error.upstream_count,
            lineaire_km=error.upstream_km,
            scale=error.scale,
            zone=error.zone_name or tr("oversize_zone_unknown", self.lang),
            max_count=SEED_FEATURE_MAX,
        ))
        go = box.addButton(tr("oversize_go", self.lang),
                           QMessageBox.ButtonRole.DestructiveRole)
        back = box.addButton(tr("oversize_back", self.lang),
                             QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(back)
        box.exec_()

        if box.clickedButton() is go:
            self._allow_oversize = True
            # Le calcul repart de ce qui est deja charge, et non de zero :
            # sur un grand bassin, la remontee du chevelu represente
            # l'essentiel de l'attente.
            self._resume = error.state
            self.log(tr("oversize_accepted", self.lang))
            # set_controls_enabled n'a pas encore ete rappele : le bloc
            # finally de _on_finished s'en charge apres notre retour. On
            # relance donc apres lui, et non d'ici.
            QTimer.singleShot(0, self.run)

    # -------------------------------------------------------------- Rapport

    def show_preview(self):
        """Apercu avant impression du dernier bassin, sans rien enregistrer.

        C'est la meme page que celle du rapport, montee par la meme fonction :
        ce qui s'affiche est ce qui sortira du PDF. La difference est qu'ici
        rien n'est ecrit - on regarde, on imprime depuis la fenetre, ou on
        ferme. Le geste naturel devient alors : voir d'abord, enregistrer
        ensuite si la page convient.

        La fenetre est modale et le panneau reste verrouille tant qu'elle est
        ouverte : la mise en page vit sur les couches memoire du bassin, qu'un
        nouveau calcul remplacerait sous ses pieds.
        """
        from ..report import builder, charts, layout as layout_module

        if self.last_result is None or self._running:
            return

        self._running = True
        self._started = time.time()
        self.set_controls_enabled(False)
        if not charts.available():
            self.log(tr("no_charts", self.lang))
        try:
            with builder.prepared_layout(
                self.last_result, self.last_layers,
                progress=lambda m: self.log("  " + str(m)),
            ) as prepared:
                page = prepared[0]
                self._status(tr("btn_preview", self.lang))
                layout_module.print_preview(
                    page, tr("btn_preview", self.lang), self,
                    export_label=tr("preview_export", self.lang),
                    on_export=lambda window: self._export_from_preview(
                        page, window),
                )
        except Exception as exc:
            self.log(tr("done_error", self.lang, error=exc))
            self._status(tr("done_error", self.lang, error=exc))
        finally:
            self._running = False
            self._started = 0.0
            self.set_controls_enabled(True)

    def show_view3d(self):
        """Ouvre le bloc-diagramme du bassin, tournant a la souris.

        Le relief a ete preleve pendant le calcul, le MNT ayant disparu
        depuis : si l'etape a echoue, la fenetre le dit plutot que de s'ouvrir
        vide. Elle est modale, comme l'apercu, et pour la meme raison - elle
        vit sur le resultat du dernier calcul.
        """
        from .view3d_dialog import View3dDialog

        if self.last_result is None or self._running:
            return
        relief = self.last_result.get("relief")
        if not relief:
            self.log(tr("view3d_missing", self.lang))
            self._status(tr("view3d_missing", self.lang))
            return
        try:
            View3dDialog(
                relief, self.lang, self, layers=self.last_layers
            ).exec_()
        except Exception as exc:
            self.log(tr("done_error", self.lang, error=exc))
            self._status(tr("done_error", self.lang, error=exc))

    def _export_from_preview(self, page, window):
        """Enregistre en PDF la page affichee dans l'apercu.

        Seul le PDF sort par ce chemin : c'est la page qu'on a sous les yeux
        qu'on enregistre, pas le rapport complet. Le classeur reste au bouton
        du panneau, qui produit les deux d'un coup.

        Le dialogue d'enregistrement est accroche a la fenetre d'apercu et non
        au panneau : sans cela il s'ouvrirait derriere elle, puisqu'elle est
        modale.
        """
        from ..report import layout as layout_module

        path, _filter = QFileDialog.getSaveFileName(
            window, tr("report_dialog", self.lang), self._default_report_path(),
            "PDF (*.pdf)"
        )
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"
        try:
            layout_module.export_pdf(page, path)
        except Exception as exc:
            self.log(tr("done_error", self.lang, error=exc))
            return
        self.log(tr("report_done", self.lang, path=path))

    @staticmethod
    def _default_report_path():
        """Chemin propose a l'enregistrement : le dossier personnel, et un nom
        qui porte la date, pour que deux rapports ne se recouvrent pas."""
        return os.path.join(
            os.path.expanduser("~"),
            "BVLIP_{0}.pdf".format(time.strftime("%Y%m%d_%H%M")),
        )

    def make_report(self):
        """Produit le rapport A4 du dernier bassin delimite."""
        from ..report import builder, charts, excel

        if self.last_result is None or self._running:
            return
        path, _filter = QFileDialog.getSaveFileName(
            self, tr("report_dialog", self.lang),
            self._default_report_path(), "PDF (*.pdf)"
        )
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"

        self._running = True
        self._started = time.time()
        self.set_controls_enabled(False)
        if not charts.available():
            self.log(tr("no_charts", self.lang))
        if not excel.available():
            self.log(tr("no_workbook", self.lang))
        try:
            produced = builder.build_report(
                self.last_result, self.last_layers, path,
                progress=lambda m: self.log("  " + str(m)),
            )
            self.log(tr("report_done", self.lang, path=produced["pdf"]))
            if produced.get("xlsx"):
                self.log(tr("report_xlsx", self.lang, path=produced["xlsx"]))
            self._status(tr(
                "report_done", self.lang,
                path=os.path.basename(produced["pdf"]),
            ))
            # La proposition d'ouvrir le dossier est une politesse, posee
            # apres coup sur des fichiers deja ecrits. Son echec ne dit rien
            # du rapport et ne doit pas le faire passer pour rate : sans ce
            # garde, un rapport complet s'affichait en "Echec" a cause d'une
            # boite de dialogue.
            try:
                self._offer_to_open(produced)
            except Exception as exc:      # noqa: BLE001 - simple confort
                self.log(tr("warning", self.lang, message=exc))
        except Exception as exc:
            self.log(tr("done_error", self.lang, error=exc))
            self._status(tr("done_error", self.lang, error=exc))
        finally:
            self._running = False
            self._started = 0.0
            self.set_controls_enabled(True)

    def _offer_to_open(self, produced):
        """Annonce le rapport dans la barre de messages de QGIS.

        Un bandeau, et non une fenetre a valider. La difference n'est pas
        cosmetique : une boite modale arrete tout et exige une reponse pour un
        travail qui est deja fait, alors que le rapport est ecrit et qu'il n'y
        a plus rien a decider. Le bandeau dit la meme chose sans interrompre,
        laisse le bouton sous la main aussi longtemps qu'on en a besoin, et
        s'efface d'un clic. C'est aussi ce que fait QGIS apres un export de
        mise en page : l'utilisateur y reconnait un geste qu'il connait deja.

        L'ouverture passe par QDesktopServices, qui delegue au gestionnaire de
        fichiers du systeme : pas de commande shell a construire, donc rien a
        echapper, rien a adapter d'un systeme a l'autre, et aucun
        sous-processus - que le depot refuserait.
        """
        paths = [p for p in (produced.get("pdf"), produced.get("xlsx")) if p]
        if not paths:
            return

        bar = self.iface.messageBar()
        widget = bar.createMessage(
            tr("report_ready_title", self.lang),
            tr("open_folder_ask", self.lang,
               files=", ".join(os.path.basename(p) for p in paths)),
        )
        button = QPushButton(tr("open_folder", self.lang), widget)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(
            lambda: self._open_folder(os.path.dirname(paths[0]), paths[0])
        )
        widget.layout().addWidget(button)
        # Sans duree : le bandeau reste tant qu'on ne l'a pas ferme. Un
        # rapport ne se consulte pas toujours dans les dix secondes qui
        # suivent, et un bouton qui disparait tout seul est un bouton perdu.
        bar.pushWidget(widget, Qgis.MessageLevel.Info)

    def _open_folder(self, folder, document):
        """Ouvre le dossier du rapport, ou le rapport lui-meme a defaut.

        Le repli n'est pas de la precaution : selon le poste, le gestionnaire
        de fichiers refuse parfois d'ouvrir un dossier alors qu'il ouvre sans
        difficulte un document qui s'y trouve. Mieux vaut alors le PDF que
        rien du tout - c'est de toute facon ce que l'utilisateur allait
        ouvrir.
        """
        if QDesktopServices.openUrl(QUrl.fromLocalFile(folder)):
            return
        # Le dossier a ete refuse. On ouvre le document, et on le dit : le
        # journal garde la trace du refus, sans quoi personne ne saurait
        # pourquoi c'est le PDF qui s'affiche et non l'explorateur.
        QDesktopServices.openUrl(QUrl.fromLocalFile(document))
        self.log(tr("open_folder_failed", self.lang, path=folder))

    def release_canvas(self):
        """Rend le canevas : outil relache et repere retire."""
        self.canvas.unsetMapTool(self.map_tool)
        self.map_tool.clear_marker()

    def closeEvent(self, event):  # noqa: N802 (API Qt)
        # Le calcul tourne en fond : il est annule plutot que de laisser une
        # tache alimenter un panneau qui n'existe plus.
        if self._running:
            self.cancel()
        self.release_canvas()
        super().closeEvent(event)
