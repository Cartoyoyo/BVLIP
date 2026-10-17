# -*- coding: utf-8 -*-
"""Dialogue "A propos" de BVLIP, sur le modele de CanaPlan.

De haut en bas : bandeau, badges, presentation, avertissement d'usage,
auteur et lien vers le changelog, badges GitHub et LinkedIn, bouton Fermer.
Le bandeau et les badges sont des images de icons/about, produites par le
generateur commun a mes plugins (qgis_about_assets.py).

Les metadonnees sont relues ligne a ligne depuis metadata.txt plutot qu'avec
configparser : le champ description multiligne de QGIS ferait echouer un
parseur INI strict.
"""

import os

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon, QPixmap
from qgis.PyQt.QtWidgets import (
    QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
)

from ..core.network import SEED_FEATURE_GUARD, SEED_FEATURE_MAX
from ..i18n import tr

PLUGIN_DIR = os.path.dirname(os.path.dirname(__file__))
ABOUT_DIR = os.path.join(PLUGIN_DIR, "icons", "about")
GITHUB_URL = "https://github.com/Cartoyoyo/BVLIP"
LINKEDIN_URL = "https://www.linkedin.com/in/ylaloux/"
# Assez large pour tenir les trois badges sur une ligne.
DIALOG_WIDTH = 500

_META_FIELDS = ("name", "version", "author", "repository")


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


def _image(name):
    return os.path.join(ABOUT_DIR, name).replace("\\", "/")


class AboutDialog(QDialog):
    """Fiche d'identite du plugin, commune a mes plugins QGIS."""

    def __init__(self, lang, parent=None):
        super().__init__(parent)
        self.lang = lang
        meta = read_metadata()
        repository = meta["repository"] or GITHUB_URL
        readme_url = repository + "/blob/main/README.md"

        self.setWindowTitle(tr("about_title", lang))
        self.setModal(True)
        self.setFixedWidth(DIALOG_WIDTH)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        icon_path = os.path.join(PLUGIN_DIR, "icons", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(14)

        banner = os.path.join(ABOUT_DIR, "logo-full.png")
        if os.path.exists(banner):
            lbl_banner = QLabel()
            lbl_banner.setPixmap(QPixmap(banner))
            lbl_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(lbl_banner)

        badges = QLabel(
            '<div style="line-height:220%">'
            '<a href="https://qgis.org"><img src="{0}"></a>&nbsp;&nbsp;'
            '<a href="{1}#sources-de-données"><img src="{2}"></a>&nbsp;&nbsp;'
            '<a href="{1}"><img src="{3}"></a>'
            '</div>'.format(_image("badge-qgis.png"), readme_url,
                            _image("badge-donnees.png"),
                            _image("badge-langue.png")))
        badges.setOpenExternalLinks(True)
        badges.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badges.setWordWrap(True)
        layout.addWidget(badges)

        layout.addWidget(self._separator())

        about = QLabel(tr("about_description", lang))
        about.setWordWrap(True)
        about.setAlignment(Qt.AlignmentFlag.AlignJustify)
        layout.addWidget(about)

        # Les seuils sont lus dans le module qui les applique, jamais
        # recopies : une fiche qui annonce une limite differente de celle
        # que le calcul oppose est pire que pas de fiche du tout.
        limits = QLabel(tr(
            "about_limits", lang,
            guard="{0:,}".format(SEED_FEATURE_GUARD).replace(",", " "),
            hard="{0:,}".format(SEED_FEATURE_MAX).replace(",", " ")))
        limits.setWordWrap(True)
        limits.setAlignment(Qt.AlignmentFlag.AlignJustify)
        limits.setStyleSheet("color:#5d6d7e;")
        layout.addWidget(limits)

        warning = QLabel("<b>{0}</b> — {1}".format(
            tr("about_warning_title", lang), tr("about_warning", lang)))
        warning.setWordWrap(True)
        warning.setAlignment(Qt.AlignmentFlag.AlignJustify)
        warning.setStyleSheet(
            "background:#FFF4E5; color:#6B4200; border:1px solid #E0A040;"
            "border-radius:4px; padding:8px;")
        layout.addWidget(warning)

        layout.addWidget(self._separator())

        author = QLabel('<b>{0}</b><br><a href="{1}#changelog">{2}</a>'.format(
            meta["author"] or "Yoan Laloux", readme_url,
            tr("version_label", lang, version=meta["version"])))
        author.setOpenExternalLinks(True)
        author.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(author)

        links = QLabel(
            '<a href="{0}"><img src="{1}"></a>&nbsp;&nbsp;'
            '<a href="{2}"><img src="{3}"></a>'.format(
                repository, _image("badge-github.png"),
                LINKEDIN_URL, _image("badge-linkedin.png")))
        links.setOpenExternalLinks(True)
        links.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(links)

        layout.addWidget(self._separator())

        btn_close = QPushButton(tr("close", lang))
        btn_close.setDefault(True)
        btn_close.setFixedWidth(100)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.accept)
        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(btn_close)
        buttons.addStretch()
        layout.addLayout(buttons)

        # Les textes a retour a la ligne trompent la taille par defaut de la
        # fenetre, qui les tronquait : la hauteur est celle que le contenu
        # demande a cette largeur, sans depasser l'ecran (720 px sur certains
        # postes).
        wanted = layout.totalHeightForWidth(DIALOG_WIDTH)
        screen = parent.screen() if parent is not None else None
        if screen is not None:
            wanted = min(wanted, int(screen.availableGeometry().height() * 0.95))
        self.setFixedHeight(wanted)

    @staticmethod
    def _separator():
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        return separator
