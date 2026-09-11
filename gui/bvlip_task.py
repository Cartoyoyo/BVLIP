# -*- coding: utf-8 -*-
"""Execution du traitement dans une tache de fond QGIS.

Jusqu'ici la chaine tournait dans le fil de l'interface, entrecoupee d'appels
a processEvents. Cela ne suffit pas : processEvents ne rend la main a Qt
qu'entre deux etapes, or l'essentiel du temps se passe *dans* des appels
bloquants qu'il ne peut pas interrompre. Sur un bassin de quelques kilometres
carres, mesure par etape : 9,8 s de telechargement de l'occupation du sol,
6,8 s de GRASS, 4,1 s de WFS, 2,9 s de WMS, et seulement 0,3 s de calcul
numerique. Vingt-six secondes de sablier sur vingt-sept.

Deux regles gouvernent ce module :

  - **rien de ce qui touche au projet ne se fait dans le fil de fond.** La
    tache produit des donnees brutes ; les couches memoire sont fabriquees et
    ajoutees au projet dans finished(), qui s'execute dans le fil principal.
    Construire une couche puis l'ajouter au projet depuis un fil secondaire
    est le moyen le plus sur de faire tomber QGIS.
  - **la tache ne parle pas a l'interface directement.** Elle emet des
    signaux ; le panneau y reagit dans son propre fil.

Ce qui tourne dans le fil de fond ne pose pas de difficulte : GRASS est un
sous-processus, GDAL est sur tant que chaque fil a ses propres jeux de
donnees, numpy et urllib n'ont aucun etat partage.
"""

import traceback

from qgis.core import Qgis, QgsMessageLog, QgsTask
from qgis.PyQt.QtCore import pyqtSignal

from ..core.dem import DemError
from ..core.delineation import DelineationError
from ..core.geoservices import GeoserviceError
from ..core.network import NetworkError, NoNetworkNearbyError, OversizeBasinError
from ..core.pipeline import run as run_pipeline


# Echecs que la chaine sait nommer : ils remontent tels quels a l'interface.
EXPECTED_FAILURES = (
    GeoserviceError, NetworkError, DemError, DelineationError,
)

TRACE_HINT = "trace complete dans le journal de QGIS, onglet BVLIP"


class BvlipTask(QgsTask):
    """Delimite un bassin versant sans bloquer l'interface."""

    # Avancement : indice d'etape, libelle.
    step = pyqtSignal(int, str)
    # Fin : resultat du pipeline (ou None), erreur (ou None). L'erreur
    # est une chaine dans le cas courant, mais l'exception elle-meme
    # quand le panneau doit pouvoir l'interroger : c'est le cas du
    # bassin hors gabarit, dont il tire les chiffres a montrer.
    finished_with = pyqtSignal(object, object)

    def __init__(self, x, y, options, description="BVLIP - bassin versant",
                 resume=None):
        super().__init__(description, QgsTask.Flag.CanCancel)
        self.x = x
        self.y = y
        self.options = options
        # Etat d'un calcul precedemment refuse, a poursuivre plutot qu'a
        # refaire. Voir network.OversizeBasinError.
        self.resume = resume
        self.result = None
        self.error = None
        self._steps = 1

    def set_step_count(self, count):
        self._steps = max(1, count)

    def run(self):  # noqa: A003 - nom impose par QgsTask
        """Corps de la tache, execute dans le fil de fond."""
        try:
            self.result = run_pipeline(
                self.x, self.y, self.options,
                progress=self._on_step,
                cancelled=self.isCanceled,
                resume=self.resume,
            )
        except (OversizeBasinError, NoNetworkNearbyError) as exc:
            # Pas un echec technique mais une decision a prendre, et
            # elle revient a l'utilisateur. L'exception remonte telle
            # quelle : le panneau a besoin de ses chiffres pour poser
            # la question, et une trace de pile n'apprendrait rien ici.
            self.error = exc
            return False
        except EXPECTED_FAILURES as exc:
            # Echecs prevus : donnee absente, service qui refuse, exutoire
            # impossible a traiter. Leur message est deja redige pour
            # l'utilisateur et se suffit a lui-meme ; y coller une trace de
            # pile de quinze lignes ne fait que noyer la phrase utile dans
            # le journal et deborder l'etiquette de statut.
            self.error = str(exc)
            return False
        except Exception as exc:            # noqa: BLE001 - remonte a l'IHM
            # Echec imprevu, lui : la trace est le seul element exploitable,
            # mais elle va au journal de QGIS et non dans le panneau, ou
            # elle serait illisible.
            QgsMessageLog.logMessage(
                traceback.format_exc(), "BVLIP", Qgis.MessageLevel.Critical
            )
            self.error = "{0}\n({1})".format(exc, TRACE_HINT)
            return False
        return self.result is not None

    def _on_step(self, index, message):
        if self.isCanceled():
            return
        self.setProgress(100.0 * index / self._steps)
        self.step.emit(index, str(message))

    def finished(self, ok):  # noqa: N802 - API QgsTask
        """Appele dans le fil principal, que la tache ait abouti ou non."""
        if self.isCanceled():
            self.finished_with.emit(None, None)
            return
        if not ok:
            self.finished_with.emit(None, self.error or "Traitement interrompu.")
            return
        self.finished_with.emit(self.result, None)
