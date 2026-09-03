# -*- coding: utf-8 -*-
"""Fenetre de reglages, ouverte depuis le menu de l'extension.

Elle ne porte que les deux accrochages de l'exutoire : on les regle une fois
et on n'y revient plus. Les etapes de calcul, elles, se decident d'un bassin a
l'autre et restent donc dans le panneau, sous la main.
"""

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QGroupBox, QLabel, QSpinBox,
    QVBoxLayout,
)

from ..i18n import tr
from . import settings


class SettingsDialog(QDialog):
    """Reglages de l'accrochage de l'exutoire."""

    def __init__(self, lang, parent=None):
        super().__init__(parent)
        self.lang = lang
        self.setWindowTitle(tr("settings_title", lang))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.setMinimumWidth(430)

        values = settings.load()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        # --- Accrochage de l'exutoire
        group_snap = QGroupBox(tr("group_snapping", lang))
        form = QFormLayout()
        self.spin_snap = QSpinBox()
        self.spin_snap.setRange(0, 500)
        self.spin_snap.setSingleStep(10)
        self.spin_snap.setSuffix(" m")
        self.spin_snap.setValue(values["snap_radius"])
        form.addRow(tr("snap_radius", lang), self.spin_snap)

        self.spin_thalweg = QSpinBox()
        self.spin_thalweg.setRange(0, 500)
        self.spin_thalweg.setSingleStep(10)
        self.spin_thalweg.setSuffix(" m")
        self.spin_thalweg.setValue(values["thalweg_radius"])
        self.spin_thalweg.setToolTip(tr("thalweg_tip", lang))
        label_thalweg = QLabel(tr("thalweg_cells", lang))
        label_thalweg.setToolTip(tr("thalweg_tip", lang))
        form.addRow(label_thalweg, self.spin_thalweg)
        group_snap.setLayout(form)
        layout.addWidget(group_snap)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.RestoreDefaults
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(
            self._restore
        )
        layout.addWidget(buttons)
        self.setLayout(layout)

    def _restore(self):
        # Seuls les reglages de cette fenetre sont ramenes a leur valeur par
        # defaut : les cases du panneau ne sont pas de son ressort.
        defaults = dict(settings.DEFAULTS_BY_KEY)
        self.spin_snap.setValue(defaults["snap_radius"])
        self.spin_thalweg.setValue(defaults["thalweg_radius"])

    def accept(self):
        settings.save({
            "snap_radius": self.spin_snap.value(),
            "thalweg_radius": self.spin_thalweg.value(),
        })
        super().accept()
