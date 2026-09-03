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

from qgis.PyQt import sip
from qgis.PyQt.QtCore import Qt, QUrl
from qgis.PyQt.QtGui import QDesktopServices, QFont
from qgis.PyQt.QtWidgets import (
    QApplication, QCheckBox, QDockWidget, QFileDialog, QGridLayout, QGroupBox,
    QLabel, QMessageBox, QProgressBar, QPushButton, QSizePolicy, QTextEdit,
    QVBoxLayout, QWidget,
)

from ..i18n import tr
from . import settings
from .outlet_map_tool import OutletMapTool

# Hauteur commune a tous les boutons du panneau.
BTN_HEIGHT = 30

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
BTN_CANCEL = (
    "QPushButton{background:#c0392b;color:#fff;border-radius:5px;"
    "font-weight:bold;font-size:11px}"
    "QPushButton:hover{background:#d44534}"
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

        self.map_tool = OutletMapTool(self.canvas)
        self.map_tool.outlet_picked.connect(self._on_outlet_picked)
        self.map_tool.deactivated.connect(self._on_tool_deactivated)

        self.setObjectName("BvlipDock")
        self._build_ui()
        self.retranslate()

    # ------------------------------------------------------------------ UI

    def _build_ui(self):
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Exutoire
        self.grp_outlet = QGroupBox()
        outlet_layout = QVBoxLayout()
        self.btn_pick = QPushButton()
        self.btn_pick.setCheckable(True)
        self.btn_pick.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pick.setStyleSheet(BTN_PICK)
        self.btn_pick.clicked.connect(self._on_pick_toggled)
        outlet_layout.addWidget(self.btn_pick)

        self.lbl_outlet = QLabel()
        font_outlet = QFont()
        font_outlet.setBold(True)
        self.lbl_outlet.setFont(font_outlet)
        self.lbl_outlet.setStyleSheet("color:#c0392b")
        outlet_layout.addWidget(self.lbl_outlet)

        self.grp_outlet.setLayout(outlet_layout)
        layout.addWidget(self.grp_outlet)

        # Etapes de calcul : elles se decident d'un bassin a l'autre, elles
        # restent donc sous la main. Les reglages d'accrochage, eux, se posent
        # une fois et vivent dans le menu de l'extension.
        self.grp_options = QGroupBox()
        options_layout = QVBoxLayout()
        stored = settings.load()
        self.chk_metrics = QCheckBox()
        self.chk_metrics.setChecked(stored["with_metrics"])
        self.chk_landcover = QCheckBox()
        self.chk_landcover.setChecked(stored["with_land_cover"])
        self.chk_refine = QCheckBox()
        self.chk_refine.setChecked(stored["refine"])
        for widget in (self.chk_metrics, self.chk_landcover, self.chk_refine):
            widget.toggled.connect(self._save_options)
            options_layout.addWidget(widget)
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

        # Tous les boutons a la meme hauteur, et les deux boutons cote a cote
        # a la meme largeur : c'est la regularite qui rend une pile de boutons
        # lisible, pas la taille de chacun.
        for button in (self.btn_pick, self.btn_run, self.btn_cancel,
                       self.btn_report):
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
        layout.addWidget(self.log_area)

        layout.addStretch()
        container.setLayout(layout)
        self.setWidget(container)

    def retranslate(self):
        """Reapplique tous les libelles dans la langue courante."""
        lang = self.lang
        self.setWindowTitle(tr("plugin_title", lang))
        self.grp_outlet.setTitle(tr("group_outlet", lang))
        self.btn_pick.setText(tr("btn_pick", lang))
        self.grp_options.setTitle(tr("group_options", lang))
        self.chk_metrics.setText(tr("opt_metrics", lang))
        self.chk_landcover.setText(tr("opt_landcover", lang))
        self.chk_refine.setText(tr("opt_refine", lang))
        self.chk_refine.setToolTip(tr("refine_tip", lang))
        self.btn_run.setText(tr("btn_run", lang))
        self.btn_cancel.setText(tr("btn_cancel", lang))
        self.btn_report.setText(tr("btn_report", lang))
        self.btn_report.setToolTip(tr("report_tip", lang))
        self.lbl_status.setText(tr("ready", lang))
        self.progress.setFormat(tr("progress_fmt", lang))
        self._refresh_outlet_label()

    # --------------------------------------------------------------- Slots

    def _save_options(self, _checked=False):
        """Les cases sont la source de verite : elles s'enregistrent aussitot.

        Le traitement relit les reglages au lancement, il n'y a donc qu'un
        seul endroit ou l'etat est conserve.
        """
        settings.save({
            "with_metrics": self.chk_metrics.isChecked(),
            "with_land_cover": self.chk_landcover.isChecked(),
            "refine": self.chk_refine.isChecked(),
        })

    def _on_pick_toggled(self, checked):
        if checked:
            self.canvas.setMapTool(self.map_tool)
        else:
            self.canvas.unsetMapTool(self.map_tool)

    def _on_tool_deactivated(self):
        self.btn_pick.setChecked(False)

    def _on_outlet_picked(self, x, y):
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
        if self._alive(self.lbl_status):
            self.lbl_status.setText(text)

    def log(self, message):
        if not self._alive(self.log_area):
            return
        self.log_area.append(message)
        QApplication.processEvents()

    def set_controls_enabled(self, enabled):
        for widget in (
            self.btn_run, self.btn_pick, self.chk_metrics,
            self.chk_landcover, self.chk_refine,
        ):
            if self._alive(widget):
                widget.setEnabled(enabled)
        if self._alive(self.btn_report):
            self.btn_report.setEnabled(
                enabled and self.last_result is not None
            )
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
        self.log_area.clear()
        if self.outlet is None:
            self.log(tr("err_no_outlet", self.lang))
            return

        # Les reglages viennent du menu de l'extension, pas du panneau : ils
        # sont relus a chaque lancement, donc une modification prend effet
        # sans rouvrir le panneau.
        options = settings.pipeline_options()

        self.last_result = None
        self._running = True
        self._started = time.time()
        self._click_of_run = self.outlet
        self.progress.setMaximum(len(STEPS))
        self.progress.setValue(0)
        self.log(tr("outlet_set", self.lang, x=self.outlet[0], y=self.outlet[1]))
        self.log(tr("running_background", self.lang))

        task = BvlipTask(self.outlet[0], self.outlet[1], options)
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

    # -------------------------------------------------------------- Rapport

    def make_report(self):
        """Produit le rapport A4 du dernier bassin delimite."""
        from ..report import builder, charts, excel

        if self.last_result is None or self._running:
            return
        default = os.path.join(
            os.path.expanduser("~"),
            "BVLIP_{0}.pdf".format(time.strftime("%Y%m%d_%H%M")),
        )
        path, _filter = QFileDialog.getSaveFileName(
            self, tr("report_dialog", self.lang), default, "PDF (*.pdf)"
        )
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"

        self._running = True
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
            self._offer_to_open(produced)
        except Exception as exc:
            self.log(tr("done_error", self.lang, error=exc))
            self._status(tr("done_error", self.lang, error=exc))
        finally:
            self._running = False
            self.set_controls_enabled(True)

    def _offer_to_open(self, produced):
        """Propose d'ouvrir le dossier ou le rapport vient d'etre ecrit.

        Le rapport part rarement seul : il y a le PDF et le classeur, souvent a
        transmettre dans la foulee. Plutot que de laisser l'utilisateur
        retrouver le chemin dans le journal, on lui ouvre l'emplacement.

        L'ouverture passe par QDesktopServices, qui delegue au gestionnaire de
        fichiers du systeme : pas de commande shell a construire, donc rien a
        echapper et rien a adapter d'un systeme a l'autre.
        """
        paths = [p for p in (produced.get("pdf"), produced.get("xlsx")) if p]
        if not paths:
            return
        folder = os.path.dirname(paths[0])

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Information)
        box.setWindowTitle(tr("report_ready_title", self.lang))
        box.setText(tr(
            "open_folder_ask", self.lang,
            files="\n".join(os.path.basename(p) for p in paths),
        ))
        box.setInformativeText(folder)
        open_button = box.addButton(tr("open_folder", self.lang),
                                    QMessageBox.ButtonRole.AcceptRole)
        box.addButton(tr("close", self.lang), QMessageBox.ButtonRole.RejectRole)
        box.exec_()

        if box.clickedButton() is open_button:
            if not QDesktopServices.openUrl(QUrl.fromLocalFile(folder)):
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
