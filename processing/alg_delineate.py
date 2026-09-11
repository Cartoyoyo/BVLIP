# -*- coding: utf-8 -*-
"""Algorithme Processing : bassins versants amont d'une couche de points.

Chaque entite de la couche d'entree donne un bassin. Les points sont reprojetes
en Lambert 93 avant traitement : c'est le systeme du RGE ALTI et de la BD TOPO,
et travailler dans un autre fausserait les distances d'accrochage.

Un point qui echoue n'interrompt pas le lot : l'erreur est journalisee et le
traitement passe au suivant. Sur une couche de dix exutoires, mieux vaut neuf
bassins et un message qu'un arret sec.
"""

import os

from qgis.core import (
    QgsCoordinateTransform, QgsCoordinateReferenceSystem, QgsFeature,
    QgsFeatureSink, QgsField, QgsFields, QgsGeometry, QgsPointXY,
    QgsProcessing, QgsProcessingAlgorithm, QgsProcessingException,
    QgsProcessingParameterBoolean, QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource, QgsProcessingParameterNumber,
    QgsProject, QgsWkbTypes,
)
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.PyQt.QtGui import QIcon

from ..core import datasets as catalogue
from ..core import results
from ..core.pipeline import PipelineOptions, run as run_pipeline

LAMBERT93 = QgsCoordinateReferenceSystem("EPSG:2154")


class DelineateWatershedAlgorithm(QgsProcessingAlgorithm):
    """Delimitation des bassins versants amont d'une couche de points."""

    INPUT = "INPUT"
    SNAP_RADIUS = "SNAP_RADIUS"
    THALWEG_RADIUS = "THALWEG_RADIUS"
    RESOLUTION = "RESOLUTION"
    SIMPLIFY_CELLS = "SIMPLIFY_CELLS"
    THRESHOLD = "THRESHOLD"
    DATASETS = "DATASETS"
    OVERSIZE = "OVERSIZE"
    SMALL_BASIN = "SMALL_BASIN"
    OUTPUT = "OUTPUT"
    OUTPUT_OUTLETS = "OUTPUT_OUTLETS"

    def tr(self, text):
        return QCoreApplication.translate("BVLIP", text)

    @staticmethod
    def _dataset_labels():
        """Intitules de la liste, dans l'ordre du catalogue.

        Ils portent le nom de leur onglet en tete faute de pouvoir les
        regrouper : Processing ne connait qu'une liste plate, et "ZNIEFF de
        type I" seul ne dirait pas de quelle famille il releve une fois pose
        au milieu des vingt et un autres.

        Les libelles ne passent pas par i18n : Processing traduit par son
        propre mecanisme, celui de Qt, et melanger les deux rendrait la
        chaine intraduisible d'un cote comme de l'autre.
        """
        return ["{0} - {1}".format(tab, key)
                for key, tab, _on in catalogue.DATASETS]

    @staticmethod
    def _dataset_defaults():
        return [index for index, (_key, _tab, on)
                in enumerate(catalogue.DATASETS) if on]

    def createInstance(self):  # noqa: N802 (API QGIS)
        return DelineateWatershedAlgorithm()

    def name(self):
        return "delimiterbassinversant"

    def displayName(self):  # noqa: N802
        return self.tr("Bassin versant amont d'un point")

    def group(self):
        return self.tr("Hydrologie")

    def groupId(self):  # noqa: N802
        return "hydrologie"

    def icon(self):
        path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "icons", "icon.png"
        )
        return QIcon(path) if os.path.exists(path) else QgsProcessingAlgorithm.icon(self)

    def shortHelpString(self):  # noqa: N802
        return self.tr(
            "Delimite, pour chaque point de la couche d'entree, le bassin "
            "versant topographique draine par ce point.\n\n"
            "Le modele numerique de terrain RGE ALTI et le reseau "
            "hydrographique BD TOPO sont telecharges automatiquement depuis "
            "la Geoplateforme IGN : aucune donnee n'est a preparer.\n\n"
            "L'exutoire est d'abord accroche sur le reseau BD TOPO, puis "
            "recale sur la maille de plus forte accumulation du MNT. Ces deux "
            "reglages sont determinants : un exutoire tombe a cote du talweg "
            "produit un bassin de quelques ares au lieu de plusieurs "
            "kilometres carres.\n\n"
            "Un exutoire dont le bassin demanderait de charger plus de "
            "80 000 troncons est refuse plutot que rendu tronque : un bassin coupe au bord de "
            "l'emprise garde l'allure d'un bassin juste et rien en aval ne "
            "sait plus qu'il est faux. Cochez alors l'option des bassins "
            "hors gabarit, ou reprenez l'exutoire plus en amont.\n\n"
            "Quand aucun cours d'eau BD TOPO n'est numerise a proximite du "
            "point - frequent en tete de bassin versant, sur les fosses et "
            "ruisseaux intermittents - le traitement echoue par defaut. "
            "L'option du mode petit bassin versant recale alors l'exutoire "
            "sur le seul MNT, sans le filtre du lineaire BD TOPO ni "
            "controle de coherence en aval : le resultat n'est pas "
            "confirme, a verifier au cas par cas.\n\n"
            "Ne fonctionne que sur le territoire francais couvert par le "
            "RGE ALTI."
        )

    # ------------------------------------------------------------ Parametres

    def initAlgorithm(self, config=None):  # noqa: N802
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.INPUT, self.tr("Exutoires (points)"),
            [QgsProcessing.TypeVectorPoint],
        ))
        self.addParameter(QgsProcessingParameterNumber(
            self.SNAP_RADIUS,
            self.tr("Rayon d'accrochage au reseau BD TOPO (m)"),
            QgsProcessingParameterNumber.Type.Double, defaultValue=50.0,
            minValue=0.0, maxValue=1000.0,
        ))
        self.addParameter(QgsProcessingParameterNumber(
            self.THALWEG_RADIUS,
            self.tr("Rayon de recalage sur le chevelu du MNT (m)"),
            QgsProcessingParameterNumber.Type.Double, defaultValue=50.0,
            minValue=0.0, maxValue=500.0,
        ))
        self.addParameter(QgsProcessingParameterNumber(
            self.RESOLUTION,
            self.tr("Resolution du MNT en metres (0 pour l'ajuster "
                    "automatiquement)"),
            QgsProcessingParameterNumber.Type.Double, defaultValue=0.0,
            minValue=0.0, maxValue=100.0,
        ))
        self.addParameter(QgsProcessingParameterNumber(
            self.SIMPLIFY_CELLS,
            self.tr("Simplification du contour (mailles)"),
            QgsProcessingParameterNumber.Type.Double, defaultValue=2.0,
            minValue=0.0, maxValue=10.0,
        ))
        self.addParameter(QgsProcessingParameterNumber(
            self.THRESHOLD,
            self.tr("Seuil d'ouverture des ecoulements (mailles)"),
            QgsProcessingParameterNumber.Type.Integer, defaultValue=200,
            minValue=10, maxValue=100000,
        ))
        # Une seule liste a choix multiple plutot que vingt-deux cases :
        # le panneau les range en onglets, ce que Processing ne sait pas
        # faire, et vingt-deux booleens dans un modele seraient illisibles.
        # L'ordre et les defauts sont ceux du catalogue, si bien qu'une
        # donnee ajoutee apparait ici sans qu'on y touche.
        self.addParameter(QgsProcessingParameterEnum(
            self.DATASETS, self.tr("Donnees a rapatrier"),
            options=self._dataset_labels(), allowMultiple=True,
            defaultValue=self._dataset_defaults(),
        ))
        self.addParameter(QgsProcessingParameterBoolean(
            self.OVERSIZE,
            self.tr("Autoriser les bassins hors gabarit (plus de 80 000 "
                    "troncons : tres long, maille grossiere)"),
            defaultValue=False,
        ))
        self.addParameter(QgsProcessingParameterBoolean(
            self.SMALL_BASIN,
            self.tr("Mode petit bassin versant : si aucun cours d'eau "
                    "BD TOPO n'est accessible autour du point, recaler "
                    "l'exutoire sur le MNT seul, sans controle de "
                    "coherence sur le reseau"),
            defaultValue=False,
        ))
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT, self.tr("Bassins versants"),
            QgsProcessing.TypeVectorPolygon,
        ))
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT_OUTLETS, self.tr("Exutoires"),
            QgsProcessing.TypeVectorPoint, optional=True,
        ))

    # -------------------------------------------------------------- Execution

    def processAlgorithm(self, parameters, context, feedback):  # noqa: N802
        source = self.parameterAsSource(parameters, self.INPUT, context)
        if source is None:
            raise QgsProcessingException(
                self.invalidSourceError(parameters, self.INPUT)
            )

        options = PipelineOptions(
            snap_radius=self.parameterAsDouble(parameters, self.SNAP_RADIUS, context),
            thalweg_radius=self.parameterAsDouble(
                parameters, self.THALWEG_RADIUS, context),
            resolution=(
                self.parameterAsDouble(parameters, self.RESOLUTION, context)
                or None
            ),
            simplify_cells=self.parameterAsDouble(parameters, self.SIMPLIFY_CELLS, context),
            stream_threshold=self.parameterAsInt(parameters, self.THRESHOLD, context),
            datasets=[
                catalogue.KEYS[index] for index in self.parameterAsEnums(
                    parameters, self.DATASETS, context)
            ],
            allow_oversize=self.parameterAsBool(
                parameters, self.OVERSIZE, context),
            allow_small_basin=self.parameterAsBool(
                parameters, self.SMALL_BASIN, context),
        )

        basin_fields = _fields(results.BASIN_FIELDS)
        outlet_fields = _fields(results.OUTLET_FIELDS)
        sink, sink_id = self.parameterAsSink(
            parameters, self.OUTPUT, context, basin_fields,
            QgsWkbTypes.Type.Polygon, LAMBERT93,
        )
        outlet_sink, outlet_id = self.parameterAsSink(
            parameters, self.OUTPUT_OUTLETS, context, outlet_fields,
            QgsWkbTypes.Type.Point, LAMBERT93,
        )

        transform = None
        if source.sourceCrs() != LAMBERT93:
            transform = QgsCoordinateTransform(
                source.sourceCrs(), LAMBERT93, QgsProject.instance()
            )

        total = source.featureCount() or 1
        succeeded = 0
        for index, feature in enumerate(source.getFeatures()):
            if feedback.isCanceled():
                break
            point = _point_of(feature, transform)
            if point is None:
                feedback.reportError(
                    self.tr("Entite {0} : geometrie ponctuelle absente, "
                            "ignoree.").format(feature.id())
                )
                continue

            label = "{0}/{1}".format(index + 1, total)
            feedback.pushInfo(
                self.tr("Exutoire {0} : {1:.1f} ; {2:.1f}").format(
                    label, point[0], point[1])
            )
            # Le repertoire de travail est laisse a la chaine, qui le cree
            # et le detruit pour chaque exutoire. En le fabriquant ici, un lot
            # de dix points laissait dix repertoires de plusieurs centaines de
            # megaoctets derriere lui.
            try:
                result = run_pipeline(
                    point[0], point[1], options,
                    progress=lambda _i, message: feedback.pushInfo(
                        "   " + str(message)),
                    feedback=None,
                    cancelled=feedback.isCanceled,
                )
            except Exception as exc:
                feedback.reportError(
                    self.tr("Exutoire {0} echoue : {1}").format(label, exc)
                )
                feedback.setProgress(100.0 * (index + 1) / total)
                continue
            if result is None:
                break

            for warning in result["avertissements"]:
                feedback.pushWarning(warning)

            basin_id = "{0}_{1}".format(
                feature.id(), source.sourceName() or "bv"
            )
            groups, basin_id = results.build_attributes(
                result["delineation"], result["network"], point,
                result["metrics"], result["water_body"], basin_id,
                result["land_cover"], result.get("affinage"),
                result.get("protected"), result.get("structures"),
                result.get("groundwater"), result.get("hydroecoregion"),
            )
            sink.addFeature(
                results.basin_feature(
                    basin_fields, result["delineation"]["geometry"], groups
                ),
                QgsFeatureSink.Flag.FastInsert,
            )
            if outlet_sink is not None:
                for item in results.outlet_features(outlet_fields, result,
                                                    point, basin_id):
                    outlet_sink.addFeature(item, QgsFeatureSink.Flag.FastInsert)

            succeeded += 1
            feedback.pushInfo(self.tr("   surface : {0:.4f} km2").format(
                result["delineation"]["area"] / 1e6))
            feedback.setProgress(100.0 * (index + 1) / total)

        feedback.pushInfo(
            self.tr("{0} bassin(s) delimite(s) sur {1}.").format(succeeded, total)
        )
        self._outputs = {self.OUTPUT: sink_id}
        if outlet_id:
            self._outputs[self.OUTPUT_OUTLETS] = outlet_id
        return dict(self._outputs)

    def postProcessAlgorithm(self, context, feedback):  # noqa: N802
        """Pose les intitules complets sur les couches produites.

        Les puits Processing ne portent que des noms de colonnes ; les alias
        ne peuvent etre appliques qu'une fois les couches chargees.
        """
        for key, definition in ((self.OUTPUT, results.BASIN_FIELDS),
                                (self.OUTPUT_OUTLETS, results.OUTLET_FIELDS)):
            layer_id = getattr(self, "_outputs", {}).get(key)
            if not layer_id:
                continue
            layer = context.getMapLayer(layer_id)
            if layer is None:
                continue
            index = {f.name(): i for i, f in enumerate(layer.fields())}
            for entry in definition:
                name, label = entry[0], entry[5]
                if label and name in index:
                    layer.setFieldAlias(index[name], label)
        return dict(getattr(self, "_outputs", {}))


# ------------------------------------------------------------------ Outils

def _fields(definition):
    fields = QgsFields()
    for entry in definition:
        name, kind, length, precision = entry[:4]
        fields.append(QgsField(name, kind, len=length, prec=precision))
    return fields


def _point_of(feature, transform):
    geometry = feature.geometry()
    if geometry.isEmpty():
        return None
    point = geometry.centroid().asPoint()
    if transform is not None:
        try:
            point = transform.transform(point)
        except Exception:
            return None
    return (point.x(), point.y())


