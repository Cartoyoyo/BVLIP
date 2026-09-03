# -*- coding: utf-8 -*-
"""Mise en page A4 du rapport, construite par le code.

Un bassin par page : la carte occupe la moitie haute, les informations et les
graphiques la moitie basse.

Le gabarit est monte par programme plutot que charge depuis un fichier .qpt.
Un .qpt fige les noms de champs et les expressions : la moindre evolution de
la table obligerait a rouvrir le gabarit dans QGIS et a le maintenir en
parallele du code. Ici, les sections du rapport se lisent dans
core.results.REPORT_SECTIONS, et les intitules avec unites viennent des alias
de la couche : ajouter une caracteristique suffit a la voir apparaitre.

Le masque est obtenu en superposant a la carte une copie du bassin rendue en
polygone inverse : tout ce qui est hors du bassin est voile de blanc, le
contexte reste lisible sans detourner l'oeil.
"""

import os

from qgis.core import (
    QgsFillSymbol, QgsInvertedPolygonRenderer, QgsLayoutExporter,
    QgsLayoutItemLabel, QgsLayoutItemMap, QgsLayoutItemPicture,
    QgsLayoutItemScaleBar, QgsLayoutMeasurement, QgsLayoutPoint,
    QgsLayoutSize, QgsPrintLayout, QgsTextFormat,
    QgsProject, QgsRasterLayer, QgsUnitTypes,
)
from qgis.PyQt.QtCore import QRectF
from qgis.PyQt.QtGui import QColor, QFont

MM = QgsUnitTypes.LayoutMillimeters
A4_WIDTH = 210.0
A4_HEIGHT = 297.0
MARGIN = 12.0

ARDOISE = QColor(44, 62, 80)
GRIS = QColor(127, 140, 141)

# Fond de plan par defaut : le Plan IGN v2, seule carte topographique servie
# librement par la Geoplateforme. Le SCAN 25 n'est pas en acces libre ; les
# rediffusions regionales existent mais ne couvrent pas tout le territoire, et
# ne peuvent donc pas etre le defaut d'un plugin diffuse a tous.
#
# L'acces passe par le fournisseur WMTS et non par une couche XYZ : sur les
# postes ou l'acces au reseau est filtre, le chargeur de tuiles XYZ echoue
# sans rien signaler et la carte du rapport sort vide, alors que le WMTS
# aboutit. Le WMTS est aussi le mode d'acces officiel du service.
PLAN_IGN_LAYER = "GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2"
PLAN_IGN_CAPABILITIES = (
    "https://data.geopf.fr/wmts"
    "?SERVICE=WMTS&VERSION=1.0.0&REQUEST=GetCapabilities"
)


def _basemap_uri(layer=PLAN_IGN_LAYER):
    import urllib.parse
    return (
        "contextualWMSLegend=0&crs=EPSG:3857&dpiMode=7&format=image/png"
        "&layers={0}&styles=normal&tileMatrixSet=PM&url={1}"
    ).format(layer, urllib.parse.quote(PLAN_IGN_CAPABILITIES, safe=""))


def _text_format(size, bold=False, color=ARDOISE):
    """Format de texte QGIS.

    setFont et setFontColor sont deprecies depuis QGIS 3.40 : la mise en forme
    des textes de mise en page passe par QgsTextFormat, qui porte la police,
    sa taille avec son unite, et la couleur en un seul objet.
    """
    font = QFont("Arial")
    font.setBold(bold)
    text_format = QgsTextFormat()
    text_format.setFont(font)
    text_format.setSize(size)
    text_format.setSizeUnit(QgsUnitTypes.RenderPoints)
    text_format.setColor(color)
    return text_format


def _label(layout, text, x, y, width, height, size=8.0, bold=False,
           color=ARDOISE, align_right=False):
    item = QgsLayoutItemLabel(layout)
    item.setText(text)
    item.setTextFormat(_text_format(size, bold, color))
    item.attemptMove(QgsLayoutPoint(x, y, MM))
    item.attemptResize(QgsLayoutSize(width, height, MM))
    if align_right:
        from qgis.PyQt.QtCore import Qt
        item.setHAlign(Qt.AlignmentFlag.AlignRight)
    layout.addLayoutItem(item)
    return item


def _picture(layout, path, x, y, width, height):
    if not path or not os.path.exists(path):
        return None
    item = QgsLayoutItemPicture(layout)
    item.setPicturePath(path)
    item.setResizeMode(QgsLayoutItemPicture.ResizeMode.ZoomResizeFrame)
    item.attemptMove(QgsLayoutPoint(x, y, MM))
    item.attemptResize(QgsLayoutSize(width, height, MM))
    layout.addLayoutItem(item)
    return item


def make_mask_layer(basin_layer):
    """Copie du bassin rendue en polygone inverse, pour voiler l'exterieur."""
    from qgis.core import QgsVectorLayer

    mask = QgsVectorLayer(
        "Polygon?crs=" + basin_layer.crs().authid(), "masque", "memory"
    )
    mask.dataProvider().addFeatures(list(basin_layer.getFeatures()))
    mask.updateExtents()
    fill = QgsFillSymbol.createSimple({
        "color": "255,255,255,190", "outline_style": "no",
    })
    mask.setRenderer(QgsInvertedPolygonRenderer.convertFromRenderer(
        mask.renderer()
    ))
    mask.renderer().setEmbeddedRenderer(
        _single_symbol_renderer(fill)
    )
    return mask


def _single_symbol_renderer(symbol):
    from qgis.core import QgsSingleSymbolRenderer
    return QgsSingleSymbolRenderer(symbol)


def _basemap():
    """Fond de plan IGN, ou None si le service n'est pas joignable."""
    layer = QgsRasterLayer(_basemap_uri(), "Plan IGN v2", "wms")
    return layer if layer.isValid() else None


def build_layout(project, layers, values, charts_paths, title=None,
                 subtitle=None):
    """Monte la mise en page et renvoie (layout, couches temporaires).

    Les couches temporaires (masque, fond de plan) doivent rester vivantes
    jusqu'a l'export : elles sont renvoyees pour que l'appelant les garde.
    """
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    page = layout.pageCollection().page(0)
    page.setPageSize(QgsLayoutSize(A4_WIDTH, A4_HEIGHT, MM))

    basin = layers["bassin"]
    temporary = []

    # ---------------------------------------------------------- En-tete
    _label(layout, title or "Bassin versant", MARGIN, 10, 150, 8,
           size=15, bold=True)
    _label(layout, subtitle or "", MARGIN, 19, 150, 6, size=8.5, color=GRIS)

    logo = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "icons", "logo.png"
    )
    _picture(layout, logo, A4_WIDTH - MARGIN - 20, 8, 20, 20)

    # ------------------------------------------------- Carte, moitie haute
    map_item = QgsLayoutItemMap(layout)
    map_item.attemptMove(QgsLayoutPoint(MARGIN, 28, MM))
    map_item.attemptResize(QgsLayoutSize(A4_WIDTH - 2 * MARGIN, 118, MM))
    map_item.setFrameEnabled(True)
    map_item.setFrameStrokeColor(GRIS)
    map_item.setFrameStrokeWidth(QgsLayoutMeasurement(0.2, MM))
    map_item.setBackgroundColor(QColor(255, 255, 255))

    mask = make_mask_layer(basin)
    temporary.append(mask)
    stack = [basin]
    if layers.get("exutoire") is not None:
        stack.insert(0, layers["exutoire"])
    if layers.get("reseau") is not None:
        stack.insert(1, layers["reseau"])
    stack.append(mask)
    base = _basemap()
    if base is not None:
        temporary.append(base)
        stack.append(base)

    project.addMapLayers(temporary, False)
    map_item.setLayers(stack)
    map_item.setKeepLayerSet(True)

    layout.addLayoutItem(map_item)

    extent = basin.extent()
    extent.grow(max(extent.width(), extent.height()) * 0.12)
    # setExtent redimensionne l'element pour respecter le rapport de forme de
    # l'emprise : le cadre carte deborderait alors sur toute la page et
    # passerait derriere le tableau. zoomToExtent conserve la taille posee.
    map_item.zoomToExtent(extent)

    scale = QgsLayoutItemScaleBar(layout)
    scale.setStyle("Single Box")
    scale.setLinkedMap(map_item)
    scale.applyDefaultSize()
    scale.setTextFormat(_text_format(7.0))
    scale.attemptMove(QgsLayoutPoint(MARGIN + 3, 136, MM))
    layout.addLayoutItem(scale)

    # ---------------------------------------- Informations, moitie basse
    _fill_bottom(layout, values, charts_paths)

    # ------------------------------------------------------------ Pied
    _label(layout,
           "Sources : RGE ALTI et BD TOPO (IGN) · Corine Land Cover 2018 · "
           "masses d'eau Sandre · fond Plan IGN v2",
           MARGIN, A4_HEIGHT - 12, A4_WIDTH - 2 * MARGIN, 5,
           size=6.5, color=GRIS)
    _label(layout, "Produit par BVLIP", A4_WIDTH - MARGIN - 60,
           A4_HEIGHT - 12, 60, 5, size=6.5, color=GRIS, align_right=True)

    return layout, temporary


def _fill_bottom(layout, values, charts_paths):
    """Deux colonnes : les valeurs a gauche, les graphiques a droite."""
    from ..core.results import ALIASES, REPORT_SECTIONS

    top = 150.0
    column_width = 88.0
    left = MARGIN
    right = MARGIN + column_width + 6

    y = top
    for section, names in REPORT_SECTIONS:
        rows = [(ALIASES.get(n, n), values.get(n)) for n in names]
        rows = [(label, v) for label, v in rows if v not in (None, "")]
        if not rows:
            continue
        if y + 5 + 3.6 * len(rows) > A4_HEIGHT - 16:
            break  # la page est pleine : le HTML porte le detail complet
        _label(layout, section, left, y, column_width, 4.5,
               size=8.0, bold=True)
        y += 5.0
        for label, value in rows:
            _label(layout, label, left, y, column_width - 26, 3.4, size=6.4)
            _label(layout, _format(value), left + column_width - 26, y, 26,
                   3.4, size=6.4, bold=True, align_right=True)
            y += 3.6
        y += 2.0

    chart_y = top
    for key, height in (("hypsometrie", 42), ("occupation", 42),
                        ("temps", 30)):
        path = (charts_paths or {}).get(key)
        if not path:
            continue
        if chart_y + height > A4_HEIGHT - 16:
            break
        _picture(layout, path, right, chart_y, column_width, height)
        chart_y += height + 3


def _format(value):
    """Presentation d'une valeur, avec l'espace insecable comme separateur
    de milliers, conformement a l'usage francais."""
    if isinstance(value, bool):
        return "oui" if value else "non"
    if isinstance(value, float):
        if abs(value) >= 1000:
            return "{:,.0f}".format(value).replace(",", " ")
        if abs(value) >= 100:
            return "{:.1f}".format(value)
        return "{:.3f}".format(value).rstrip("0").rstrip(".")
    if isinstance(value, int):
        return "{:,}".format(value).replace(",", " ")
    text = str(value)
    return text if len(text) <= 46 else text[:45] + "…"


def export_pdf(layout, path, dpi=200):
    """Exporte la mise en page en PDF et renvoie le chemin."""
    exporter = QgsLayoutExporter(layout)
    settings = QgsLayoutExporter.PdfExportSettings()
    settings.dpi = dpi
    settings.rasterizeWholeImage = False
    result = exporter.exportToPdf(path, settings)
    if result != QgsLayoutExporter.ExportResult.Success:
        raise RuntimeError(
            "Export PDF impossible ({0}). Le fichier est peut-etre ouvert "
            "dans un lecteur.".format(result)
        )
    return path
