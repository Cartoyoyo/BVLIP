# -*- coding: utf-8 -*-
"""Dialogue "A propos" de BVLIP.

Les metadonnees sont relues ligne a ligne depuis metadata.txt plutot qu'avec
configparser : le champ description multiligne de QGIS ferait echouer un
parseur INI strict.
"""

import os

from qgis.PyQt.QtCore import Qt, QUrl
from qgis.PyQt.QtGui import QDesktopServices, QFont, QPixmap
from qgis.PyQt.QtWidgets import (
    QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
)

from ..i18n import tr

PLUGIN_DIR = os.path.dirname(os.path.dirname(__file__))
LINKEDIN_URL = "https://www.linkedin.com/in/ylaloux/"
LICENSE_URL = "https://www.gnu.org/licenses/gpl-3.0.html"

_META_FIELDS = ("name", "version", "author", "email", "tracker", "repository")


def read_metadata():
    """Renvoie les champs simples de metadata.txt, avec des valeurs de repli."""
    values = {field: "" for field in _META_FIELDS}
    values["name"] = "BVLIP"
    values["version"] = "?"
    meta_path = os.path.join(PLUGIN_DIR, "metadata.txt")
    if not os.path.exists(meta_path):
        return values
    with open(meta_path, encoding="utf-8") as handle:
        for line in handle:
            for field in _META_FIELDS:
                if line.startswith(field + "="):
                    values[field] = line.split("=", 1)[1].strip()
                    break
    return values


class AboutDialog(QDialog):
    """Fiche d'identite du plugin : version, auteur, licence, signalement."""

    def __init__(self, lang, parent=None):
        super().__init__(parent)
        self.lang = lang
        meta = read_metadata()

        self.setWindowTitle(tr("about_title", lang))
        self.setFixedWidth(430)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        logo_path = os.path.join(PLUGIN_DIR, "icons", "logo.png")
        if os.path.exists(logo_path):
            lbl_logo = QLabel()
            lbl_logo.setPixmap(
                QPixmap(logo_path).scaledToWidth(160, Qt.TransformationMode.SmoothTransformation)
            )
            lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(lbl_logo)

        font_title = QFont()
        font_title.setBold(True)
        font_title.setPointSize(13)
        lbl_name = QLabel(meta["name"])
        lbl_name.setFont(font_title)
        lbl_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_name)

        lbl_version = QLabel(tr("version_label", lang, version=meta["version"]))
        lbl_version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_version)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        author = meta["author"] or "Yoan Laloux"
        layout.addWidget(
            self._link('<a href="{0}">{1}</a>'.format(LINKEDIN_URL, author))
        )
        if meta["email"]:
            layout.addWidget(
                self._link(
                    '<a href="mailto:{0}">{0}</a>'.format(meta["email"])
                )
            )
        layout.addWidget(
            self._link('<a href="{0}">GNU GPL v3</a>'.format(LICENSE_URL))
        )
        if meta["repository"]:
            layout.addWidget(
                self._link(
                    '<a href="{0}">{1}</a>'.format(
                        meta["repository"],
                        meta["repository"].replace("https://", ""),
                    )
                )
            )

        credit = QLabel(tr("data_credit", lang))
        credit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credit.setWordWrap(True)
        credit.setStyleSheet("color:#7f8c8d;font-size:10px")
        layout.addWidget(credit)

        buttons = QHBoxLayout()
        if meta["tracker"]:
            btn_bug = QPushButton(tr("report_bug", lang))
            btn_bug.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_bug.setStyleSheet(
                "QPushButton{background:#c0392b;color:#fff;border-radius:5px;"
                "font-weight:bold;font-size:11px;padding:6px 12px}"
                "QPushButton:hover{background:#d44534}"
            )
            tracker_url = meta["tracker"]
            btn_bug.clicked.connect(
                lambda: QDesktopServices.openUrl(QUrl(tracker_url))
            )
            buttons.addWidget(btn_bug)
        buttons.addStretch()
        btn_close = QPushButton(tr("close", lang))
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.accept)
        buttons.addWidget(btn_close)
        layout.addLayout(buttons)

        self.setLayout(layout)

    @staticmethod
    def _link(html):
        label = QLabel(html)
        label.setOpenExternalLinks(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label
