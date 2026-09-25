# -*- coding: utf-8 -*-
"""Vue web du relief : la page HTML de l'export 3D, affichee dans QGIS.

C'est la page de report/export3d.html_page, telle qu'on l'exporte, posee dans
un navigateur embarque plutot qu'ouverte a part. Deux moteurs possibles :

- QtWebEngine (Chromium), s'il est installe - ce sera le cas des versions de
  QGIS en Qt6 ; rien de particulier a faire, WebGL y marche d'emblee ;
- QtWebKit, le seul fourni avec QGIS 3 en Qt5 sous Windows. Il ne fait que
  du WebGL 1 (d'ou la page en WebGL 1) et demande deux precautions,
  verifiees sur QGIS 3.44 / pilote Intel :

  * pas d'"accelerated compositing" : active, la page reste blanche, texte
    compris - le calque accelere n'est jamais compose dans le widget ;
  * un contexte OpenGL de compatibilite a la creation du canevas WebGL.
    QGIS impose par defaut un profil "core" 4.3 (pour sa vue 3D), ou le
    traducteur de shaders de WebKit produit un code que le pilote refuse
    ("#version directive must occur before anything else") : aucun shader
    ne compile. Le format par defaut est donc bascule le temps du
    chargement de la page, puis rendu a QGIS.

La page est ecrite dans un fichier temporaire plutot que passee par setHtml :
QtWebEngine plafonne setHtml a 2 Mo, que la texture depasse vite. Le fichier
est supprime au prochain chargement et a la fermeture (cleanup).
"""

import os
import tempfile

from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QSurfaceFormat
from qgis.PyQt.QtWidgets import QVBoxLayout, QWidget


def _engine_view():
    """Vue QtWebEngine, ou None si le module manque (QGIS 3 en Qt5)."""
    try:
        from qgis.PyQt.QtWebEngineWidgets import QWebEngineView
    except Exception:       # noqa: BLE001 - ImportError, ou module mal lie
        return None
    return QWebEngineView()


def _webkit_view():
    """Vue QtWebKit reglee pour WebGL, ou None si le module manque."""
    try:
        from qgis.PyQt.QtWebKit import QWebSettings
        from qgis.PyQt.QtWebKitWidgets import QWebView
    except Exception:       # noqa: BLE001
        return None
    view = QWebView()
    settings = view.settings()
    settings.setAttribute(QWebSettings.WebAttribute.WebGLEnabled, True)
    settings.setAttribute(
        QWebSettings.WebAttribute.AcceleratedCompositingEnabled, False
    )
    return view


class WebReliefView(QWidget):
    """Navigateur embarque qui affiche la page 3D et la pilote."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.engine = None
        self.view = _engine_view()
        if self.view is not None:
            self.engine = "webengine"
        else:
            self.view = _webkit_view()
            if self.view is not None:
                self.engine = "webkit"
        self._path = None
        self._saved_format = None

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        if self.view is not None:
            layout.addWidget(self.view)
            self.view.loadFinished.connect(self._restore_format)
        self.setLayout(layout)

    @property
    def available(self):
        return self.view is not None

    def show_page(self, html):
        """Charge la page, a la position de camera de la page precedente.

        La camera passe par l'adresse (#cam=...) ; sous QtWebEngine, ou le
        JavaScript ne repond qu'en differe, elle repart de la vue de depart.
        """
        if self.view is None:
            return
        camera = self._camera()
        self.cleanup()
        handle, path = tempfile.mkstemp(prefix="bvlip_3d_", suffix=".html")
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(html)
        self._path = path
        if self.engine == "webkit":
            self._use_compatibility_format()
        url = QUrl.fromLocalFile(path)
        if camera:
            url.setFragment("cam=" + camera)
        self.view.load(url)

    def _camera(self):
        """Position de camera de la page affichee, ou chaine vide."""
        if self.engine != "webkit" or not self._path:
            return ""
        value = self.view.page().mainFrame().evaluateJavaScript(
            "window.bvlip ? window.bvlip.camera() : ''")
        return value if isinstance(value, str) else ""

    def run_js(self, script):
        """Execute du JavaScript dans la page, sans attendre de resultat."""
        if self.view is None:
            return
        if self.engine == "webengine":
            self.view.page().runJavaScript(script)
        else:
            self.view.page().mainFrame().evaluateJavaScript(script)

    def grab_image(self):
        """Image (QPixmap) de la page telle qu'affichee.

        Possible parce que l'"accelerated compositing" est coupe : le rendu
        WebGL est alors peint dans le widget lui-meme, que grab() recopie.
        """
        return self.view.grab()

    def cleanup(self):
        """Rend le format OpenGL a QGIS et supprime le fichier temporaire."""
        self._restore_format()
        if self._path:
            try:
                os.remove(self._path)
            except OSError:
                pass
            self._path = None

    def _use_compatibility_format(self):
        if self._saved_format is not None:
            return
        current = QSurfaceFormat.defaultFormat()
        self._saved_format = QSurfaceFormat(current)
        compat = QSurfaceFormat(current)
        compat.setProfile(
            QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile
        )
        compat.setVersion(2, 1)
        QSurfaceFormat.setDefaultFormat(compat)

    def _restore_format(self, *_args):
        if self._saved_format is not None:
            QSurfaceFormat.setDefaultFormat(self._saved_format)
            self._saved_format = None
