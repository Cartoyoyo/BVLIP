# -*- coding: utf-8 -*-
"""Fenetre d'apercu du relief, tournante a la souris.

C'est le meme bloc-diagramme que celui du rapport - la meme fonction le
dessine - mais pose sur un canevas Qt plutot que dans une image : on tourne le
bassin, on l'incline, on le regarde du dessus.

Le moteur 3D de QGIS aurait ete plus beau, mais il n'est pas pilotable depuis
Python sur les versions visees : Qgs3DMapCanvas n'expose pas de quoi lui poser
ses reglages de carte. matplotlib, lui, est deja la pour les graphiques du
rapport, ne demande aucune carte graphique, et fonctionne donc aussi en bureau
a distance - ou la 3D de QGIS reste noire.

La contrepartie est le prix d'une image : matplotlib redessine toute la
surface a chaque mouvement. La grille est donc allegee pour cette vue, bien
plus que pour l'image du rapport, sans quoi la rotation serait insupportable.
"""

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
)

from ..i18n import tr
from ..report import charts

# Points de vue proposes : le sud-ouest, qui donne du volume au relief, et le
# dessus, qui redonne la forme du bassin telle qu'on la lit sur une carte.
VIEWS = {
    "sw": (42.0, -125.0),
    "top": (89.0, -90.0),
}


class View3dDialog(QDialog):
    """Bloc-diagramme du bassin, oriente a la souris."""

    def __init__(self, relief, lang, parent=None):
        super().__init__(parent)
        self.relief = relief
        self.lang = lang
        self.setWindowTitle(tr("btn_view3d", lang))
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )
        self.resize(860, 720)

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self.axes = None
        self.canvas = self._build_canvas()
        if self.canvas is None:
            layout.addWidget(QLabel(tr("view3d_missing", lang)))
        else:
            layout.addWidget(self.canvas, 1)
            layout.addWidget(QLabel(tr("view3d_hint", lang)))

        layout.addLayout(self._build_buttons())
        self.setLayout(layout)

    # ------------------------------------------------------------- Montage

    def _build_canvas(self):
        """Canevas matplotlib portant le bloc-diagramme, ou None."""
        try:
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
        except ImportError:      # matplotlib d'avant 3.5
            try:
                from matplotlib.backends.backend_qt5agg import (
                    FigureCanvasQTAgg,
                )
            except ImportError:
                return None
        from matplotlib.figure import Figure

        # Figure construite a la main, sans passer par pyplot : c'est la seule
        # facon d'attacher un canevas Qt sans que matplotlib n'ouvre en plus sa
        # propre fenetre.
        figure = Figure(figsize=(8.5, 6.5), facecolor="white")
        self.axes = charts.relief_figure(
            self.relief, figure,
            decimate=charts.RELIEF_DECIMATE_LIVE,
        )
        if self.axes is None:
            return None
        return FigureCanvasQTAgg(figure)

    def _build_buttons(self):
        row = QHBoxLayout()
        row.setSpacing(6)
        self.btn_sw = QPushButton(tr("view3d_sw", self.lang))
        self.btn_sw.clicked.connect(lambda: self._look("sw"))
        self.btn_top = QPushButton(tr("view3d_top", self.lang))
        self.btn_top.clicked.connect(lambda: self._look("top"))
        close = QPushButton(tr("close", self.lang))
        close.clicked.connect(self.accept)
        for button in (self.btn_sw, self.btn_top, close):
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setMinimumHeight(28)
        row.addWidget(self.btn_sw)
        row.addWidget(self.btn_top)
        row.addStretch()
        row.addWidget(close)
        for button in (self.btn_sw, self.btn_top):
            button.setEnabled(self.axes is not None)
        return row

    # -------------------------------------------------------------- Actions

    def _look(self, name):
        """Ramene la vue a un point de vue nomme."""
        if self.axes is None or self.canvas is None:
            return
        elevation, azimuth = VIEWS[name]
        self.axes.view_init(elev=elevation, azim=azimuth)
        self.canvas.draw_idle()
