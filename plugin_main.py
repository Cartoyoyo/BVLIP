# -*- coding: utf-8 -*-
"""Classe principale du plugin BVLIP.

Ne fait qu'installer les entrees dans QGIS et gerer le cycle de vie du
panneau. Les imports lourds (interface, traitement) sont differes dans les
gestionnaires d'action pour que le chargement de QGIS reste rapide et qu'une
erreur de code ne bloque pas le demarrage.

Le menu de l'extension porte tout ce qui ne sert pas a chaque usage : les
reglages d'accrochage, le choix de la langue, la fiche du plugin. Le panneau
n'en est que plus court, et ce qu'on y voit est ce dont on se sert.
"""

import os

from qgis.core import Qgis, QgsApplication, QgsMessageLog
from qgis.PyQt.QtCore import QSettings, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QActionGroup, QMenu

from .i18n import LANGUAGES, resolve_language, tr

PLUGIN_DIR = os.path.dirname(__file__)


class BvlipPlugin:
    """Point d'entree QGIS : barre d'outils, menu, panneau lateral."""

    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.menu = None
        self.actions = []
        self.language_actions = {}
        self.dock = None
        self.provider = None
        self.lang = self._initial_language()

    def _initial_language(self):
        """Langue retenue : celle choisie dans le menu, sinon celle de QGIS."""
        from .gui import settings

        chosen = settings.load().get("language")
        if chosen:
            return resolve_language(chosen)
        return resolve_language(
            QSettings().value("locale/userLocale", "en_US")
        )

    # ------------------------------------------------------- Cycle de vie

    def initGui(self):  # noqa: N802 (API QGIS)
        self._sweep_workdirs()
        self._init_processing()
        icon = QIcon(os.path.join(PLUGIN_DIR, "icons", "icon.png"))

        self.action = QAction(icon, tr("action_open", self.lang),
                              self.iface.mainWindow())
        self.action.setToolTip(tr("action_tooltip", self.lang))
        self.action.setCheckable(True)
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)

        self._build_menu(icon)

    @staticmethod
    def _sweep_workdirs():
        """Efface les repertoires de travail qu'une session passee a oublies.

        Au demarrage, une fois, et sans jamais faire echouer le chargement du
        plugin : un menage rate n'est pas une raison de priver l'utilisateur
        de l'extension.
        """
        try:
            from .core.pipeline import sweep_workdirs
            removed = sweep_workdirs()
        except Exception:      # noqa: BLE001 - le menage n'est pas critique
            return
        if removed:
            QgsMessageLog.logMessage(
                "{0} repertoire(s) de travail abandonne(s) efface(s).".format(
                    removed),
                "BVLIP", Qgis.MessageLevel.Info,
            )

    def _build_menu(self, icon):
        """Sous-menu de l'extension : panneau, reglages, langue, a propos."""
        main_window = self.iface.mainWindow()
        self.menu = QMenu(tr("menu_title", self.lang).replace("&", ""),
                          main_window)
        self.menu.setIcon(icon)
        self.menu.addAction(self.action)
        self.menu.addSeparator()

        self.action_settings = QAction(tr("menu_settings", self.lang),
                                       main_window)
        self.action_settings.triggered.connect(self.open_settings)
        self.menu.addAction(self.action_settings)

        self.language_menu = self.menu.addMenu(tr("language", self.lang))
        group = QActionGroup(main_window)
        group.setExclusive(True)
        for code, label in LANGUAGES:
            action = QAction(label, main_window)
            action.setCheckable(True)
            action.setChecked(code == self.lang)
            action.triggered.connect(
                lambda _checked, c=code: self.set_language(c)
            )
            group.addAction(action)
            self.language_menu.addAction(action)
            self.language_actions[code] = action

        self.menu.addSeparator()
        self.action_about = QAction(tr("about", self.lang), main_window)
        self.action_about.triggered.connect(self.show_about)
        self.menu.addAction(self.action_about)

        self.iface.pluginMenu().addMenu(self.menu)

    def unload(self):
        if self.provider is not None:
            QgsApplication.processingRegistry().removeProvider(self.provider)
            self.provider = None
        if self.dock is not None:
            # deleteLater ne declenche pas closeEvent : le repere de
            # l'exutoire resterait sur le canevas, qui en a la propriete.
            self.dock.release_canvas()
            self.iface.removeDockWidget(self.dock)
            self.dock.deleteLater()
            self.dock = None
        if self.menu is not None:
            self.iface.pluginMenu().removeAction(self.menu.menuAction())
            self.menu.deleteLater()
            self.menu = None
        if self.action is not None:
            self.iface.removeToolBarIcon(self.action)
            self.action = None

    def _init_processing(self):
        """Enregistre le fournisseur d'algorithmes.

        L'import est differe : une erreur dans le code des algorithmes ne doit
        pas empecher le panneau de se charger.
        """
        try:
            from .processing.provider import BvlipProvider
        except ImportError:
            return
        self.provider = BvlipProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    # ------------------------------------------------------------ Panneau

    def run(self, checked=True):
        """Affiche ou masque le panneau, en le creant a la premiere demande."""
        if self.dock is None:
            from .gui.bvlip_dock import BvlipDock
            self.dock = BvlipDock(self.iface, self.lang,
                                  self.iface.mainWindow())
            self.dock.visibilityChanged.connect(self._on_dock_visibility)
            self.iface.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock)
        self.dock.setVisible(checked)
        if checked:
            self.dock.raise_()

    def _on_dock_visibility(self, visible):
        """Garde l'etat du bouton de barre d'outils synchronise avec le panneau."""
        if self.action is not None:
            self.action.setChecked(visible)

    # ------------------------------------------------------------- Actions

    def open_settings(self):
        from .gui.settings_dialog import SettingsDialog
        SettingsDialog(self.lang, self.iface.mainWindow()).exec_()

    def show_about(self):
        from .gui.about_dialog import AboutDialog
        AboutDialog(self.lang, self.iface.mainWindow()).exec_()

    def set_language(self, code):
        """Change la langue de toute l'interface du plugin."""
        from .gui import settings

        if code == self.lang:
            return
        self.lang = code
        settings.save({"language": code})
        self._retranslate()
        if self.dock is not None:
            self.dock.lang = code
            self.dock.retranslate()

    def _retranslate(self):
        if self.action is not None:
            self.action.setText(tr("action_open", self.lang))
            self.action.setToolTip(tr("action_tooltip", self.lang))
        if self.menu is not None:
            self.menu.setTitle(tr("menu_title", self.lang).replace("&", ""))
            self.action_settings.setText(tr("menu_settings", self.lang))
            self.language_menu.setTitle(tr("language", self.lang))
            self.action_about.setText(tr("about", self.lang))
        for code, action in self.language_actions.items():
            action.setChecked(code == self.lang)
