# -*- coding: utf-8 -*-
"""Rend icons/icon.png et icons/logo.png depuis icons/bvlip.svg.

    python-qgis tools/make_icons.py

Le SVG est la seule source : les deux PNG en derivent, et il n'y a donc qu'un
fichier a reprendre quand le dessin change. QGIS accepterait un SVG comme
icone de barre d'outils, mais pas les fiches de plugins.qgis.org ni GitHub,
qui attendent une image matricielle.

Le rendu passe par QtSvg, livre avec QGIS : aucune bibliotheque
supplementaire a installer. Le script se lance donc avec le Python de QGIS
(python-qgis-ltr.bat sous Windows), pas avec un Python systeme.
"""

import os
import sys

ICONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(
    __file__))), "icons")
SOURCE = os.path.join(ICONS_DIR, "bvlip.svg")

# icon.png sert la barre d'outils et la fiche du depot ; logo.png la fenetre
# A propos et l'en-tete du README, ou il est affiche plus grand.
SIZES = (("icon.png", 96), ("logo.png", 320))


def render(size):
    from qgis.PyQt.QtCore import Qt
    from qgis.PyQt.QtGui import QImage, QPainter
    from qgis.PyQt.QtSvg import QSvgRenderer

    renderer = QSvgRenderer(SOURCE)
    if not renderer.isValid():
        raise SystemExit("SVG illisible : {0}".format(SOURCE))

    # Fond transparent : l'icone doit se poser aussi bien sur un theme clair
    # que sombre, et le logo sur la page blanche du README.
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    renderer.render(painter)
    painter.end()
    return image


def main():
    if not os.path.exists(SOURCE):
        raise SystemExit("Source absente : {0}".format(SOURCE))
    for name, size in SIZES:
        target = os.path.join(ICONS_DIR, name)
        if not render(size).save(target, "PNG"):
            raise SystemExit("Ecriture impossible : {0}".format(target))
        print("{0:<10} {1:>4} px  {2:>5} octets".format(
            name, size, os.path.getsize(target)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
