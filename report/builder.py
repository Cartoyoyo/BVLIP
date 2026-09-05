# -*- coding: utf-8 -*-
"""Production du rapport : graphiques, mise en page A4, PDF et tableur.

Le PDF vient de la mise en page QGIS, le classeur est ecrit par openpyxl.
Aucun convertisseur externe n'est necessaire, ce qui evite d'imposer une
dependance a l'utilisateur pour une simple sortie de document.

Les fichiers intermediaires (graphiques, image de carte) sont produits dans un
dossier temporaire et ne survivent pas a la session : seuls le PDF et le
classeur, tous deux autonomes, restent a l'endroit choisi par l'utilisateur.
"""

import os
import shutil
import tempfile
from contextlib import contextmanager

from qgis.core import QgsLayoutExporter, QgsProject
from qgis.PyQt.QtCore import QRectF, QSize

from . import charts, excel, layout as layout_module


def _title_of(values):
    """Intitule du rapport : le nom du cours d'eau s'il est connu, sinon la
    zone hydrographique, sinon l'identifiant."""
    for key in ("cours_d_eau", "zone_hydro"):
        value = values.get(key)
        if value:
            # La BD TOPO empile parfois plusieurs denominations separees par
            # une barre oblique, souvent la meme repetee : on garde la
            # premiere, qui est la denomination principale.
            first = str(value).split("/")[0].strip()
            return "Bassin versant — {0}".format(
                first[:1].upper() + first[1:]
            )
    return "Bassin versant {0}".format(values.get("id_bv", ""))


def _subtitle_of(values):
    bits = []
    if values.get("surface_km2") is not None:
        bits.append("{0:.3f} km² ({1:.1f} ha)".format(
            values["surface_km2"], values.get("surface_ha", 0.0)))
    if values.get("me_code_eu"):
        bits.append("masse d'eau {0}".format(values["me_code_eu"]))
    if values.get("x_exutoire") is not None:
        bits.append("exutoire {0:.0f} ; {1:.0f} (Lambert 93)".format(
            values["x_exutoire"], values["y_exutoire"]))
    if values.get("date_calcul"):
        bits.append(values["date_calcul"])
    return " · ".join(bits)


def _values_of(layers):
    """Attributs du bassin, lus sur la couche, alias compris."""
    basin = layers["bassin"]
    feature = next(basin.getFeatures(), None)
    if feature is None:
        raise RuntimeError("La couche du bassin versant est vide.")
    return {field.name(): feature[field.name()] for field in basin.fields()}


def _map_image(layout, path, dpi=150):
    """Rend le seul cadre carte en PNG, pour le classeur.

    exportToImage ne sait exporter que des pages entieres : on passe donc par
    le rendu d'une region, delimitee par le rectangle du cadre carte dans les
    coordonnees de la mise en page.
    """
    item = None
    for candidate in layout.items():
        if candidate.__class__.__name__ == "QgsLayoutItemMap":
            item = candidate
            break
    if item is None:
        return None
    region = QRectF(item.pos().x(), item.pos().y(),
                    item.rect().width(), item.rect().height())
    image = QgsLayoutExporter(layout).renderRegionToImage(region, QSize(), dpi)
    if image is None or image.isNull():
        return None
    return path if image.save(path, "PNG") else None


@contextmanager
def prepared_layout(result, layers, progress=None):
    """Monte la page A4 du bassin, la tient le temps qu'on s'en serve, puis
    fait le menage.

    Deux usages la demandent : l'export du rapport et l'apercu avant
    impression. Elle est donc montee ici une fois pour toutes, plutot que dans
    chacun d'eux - c'est la seule facon de garantir que ce qui s'affiche a
    l'ecran est exactement ce qui sortira du PDF.

    Rend (mise en page, valeurs du bassin, chemins des graphiques, repertoire
    de travail). Le menage a la sortie porte sur les couches de service -
    masque, fond de plan - qui encombreraient le projet, et sur les fichiers
    intermediaires, qui n'ont plus de lecteur.
    """
    def report(message):
        if progress is not None:
            progress(message)

    values = _values_of(layers)
    workdir = tempfile.mkdtemp(prefix="bvlip_rapport_")
    project = QgsProject.instance()
    temporary = []
    try:
        report("Graphiques...")
        charts_paths = charts.build_all(
            result.get("metrics"), result.get("land_cover"), workdir,
            relief=result.get("relief"), protected=result.get("protected"),
        )
        report("Mise en page A4...")
        page, temporary = layout_module.build_layout(
            project, layers, values, charts_paths,
            title=_title_of(values), subtitle=_subtitle_of(values),
            # La seconde page vit de listes, que la table du bassin ne peut
            # pas porter : elle les prend directement dans le resultat.
            details={
                "land_cover": result.get("land_cover"),
                "agriculture": result.get("agriculture"),
                "protected": result.get("protected"),
                "structures": result.get("structures"),
                "water_body": result.get("water_body"),
                "groundwater": result.get("groundwater"),
                "hydroecoregion": result.get("hydroecoregion"),
            },
        )
        yield page, values, charts_paths, workdir
    finally:
        for layer in temporary:
            project.removeMapLayer(layer.id())
        shutil.rmtree(workdir, ignore_errors=True)


def build_report(result, layers, pdf_path, with_workbook=True, progress=None):
    """Produit le rapport du bassin et renvoie les chemins ecrits.

    result est le dictionnaire du pipeline, layers celui des couches memoire.
    Renvoie {"pdf": ..., "xlsx": ... ou None}.
    """
    def report(message):
        if progress is not None:
            progress(message)

    with prepared_layout(result, layers, progress) as prepared:
        page, values, charts_paths, workdir = prepared

        report("Export PDF...")
        layout_module.export_pdf(page, pdf_path)

        produced = {"pdf": pdf_path, "xlsx": None}
        if with_workbook:
            report("Export tableur...")
            map_png = _map_image(page, os.path.join(workdir, "carte.png"))
            xlsx_path = os.path.splitext(pdf_path)[0] + ".xlsx"
            produced["xlsx"] = excel.build_workbook(
                values, result.get("land_cover"), layers.get("reseau"),
                charts_paths, map_png, xlsx_path,
                _title_of(values), _subtitle_of(values),
                protected=result.get("protected"),
                structures=result.get("structures"),
            )
        return produced
