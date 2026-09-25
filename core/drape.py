# -*- coding: utf-8 -*-
"""Habillage du bloc-diagramme 3D par les couches thematiques du projet.

Le relief seul ne dit rien de l'occupation du sol : ce module rend une
couche vectorielle deja stylee dans le projet (BD Foret, RPG, agriculture
biologique) en image, cadree exactement sur l'emprise du relief et a sa
resolution. Le rendu QGIS lui-meme fait le travail de legende - plutot que
de recopier a la main une palette de couleurs qui finirait par diverger du
style effectivement affiche dans le projet.

Corine Land Cover est un cas a part : ses polygones sont volontairement
oublies une fois les statistiques du rapport calculees (core/landcover.py),
pour ne pas garder en memoire un chevelu qui peut peser plusieurs centaines
de megaoctets sur un grand bassin. L'habillage 3D le retelecharge donc a la
demande, sur la seule emprise du relief - bien plus petite que l'emprise du
reseau hydrographique qui a servi a delimiter le bassin - et le garde en
memoire pour la duree de l'apercu seulement.
"""

import json

from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtGui import QColor, QImage, QPainter
from qgis.core import (
    QgsCategorizedSymbolRenderer, QgsCoordinateReferenceSystem, QgsFeature,
    QgsField, QgsFields, QgsFillSymbol, QgsGeometry, QgsJsonUtils,
    QgsMapRendererCustomPainterJob, QgsMapSettings, QgsRectangle,
    QgsRendererCategory, QgsVectorLayer,
)

from .geoservices import wfs_pages
from .landcover import CLC_LEVEL1, LAYER_CLC
from .results import S, _MODERN_FIELDS

LAMBERT93 = QgsCoordinateReferenceSystem("EPSG:2154")

# Meme palette que le diagramme "Occupation du sol" du rapport (report/
# charts.py) : la encore, mieux vaut une seule source de couleurs que deux
# qui pourraient un jour diverger.
CLC_LEVEL1_COLORS = {
    "1": "#c0392b", "2": "#e6b422", "3": "#27ae60", "4": "#8e44ad",
    "5": "#2980b9",
}


def render_layer_texture(layers, x, y):
    """Rend une ou plusieurs couches en image RVBA (lignes = y du nord au
    sud, colonnes = x), superposees dans l'ordre donne.

    layers accepte une couche seule ou une liste ordonnee du dessus vers le
    dessous - meme convention que QgsMapSettings.setLayers : c'est ainsi que
    le parcellaire RPG et les parcelles bio s'habillent ensemble, chacun
    visible la ou l'autre n'a rien a montrer.

    Le fond est transparent et non blanc, et c'est ce qui permet a l'appelant
    d'empiler plusieurs habillages : la ou une couche n'a rien trace, on doit
    voir ce qui est dessous - le relief en niveaux de gris, ou un autre
    habillage - et non un aplat blanc qui masquerait tout.

    L'emprise couvre exactement les centres de maille fournis, demi-maille
    de marge comprise : chaque pixel de la texture retombe ainsi pile sur le
    sommet du maillage qu'il colore, sans decalage a l'affichage.
    """
    import numpy as np

    if not isinstance(layers, (list, tuple)):
        layers = [layers]
    layers = [layer for layer in layers if layer is not None]
    if not layers:
        return None

    cols, rows = len(x), len(y)
    half_x = abs(x[1] - x[0]) / 2.0 if cols > 1 else 1.0
    half_y = abs(y[0] - y[1]) / 2.0 if rows > 1 else 1.0
    extent = QgsRectangle(
        x[0] - half_x, y[-1] - half_y, x[-1] + half_x, y[0] + half_y,
    )

    settings = QgsMapSettings()
    settings.setLayers(layers)
    settings.setDestinationCrs(LAMBERT93)
    settings.setExtent(extent)
    settings.setOutputSize(QSize(cols, rows))
    settings.setBackgroundColor(QColor(0, 0, 0, 0))

    image = QImage(cols, rows, QImage.Format.Format_ARGB32)
    image.fill(QColor(0, 0, 0, 0))
    painter = QPainter(image)
    try:
        job = QgsMapRendererCustomPainterJob(settings, painter)
        job.renderSynchronously()
    finally:
        painter.end()

    # RGBA8888 range les octets dans l'ordre R, G, B, A en memoire, quel que
    # soit le boutisme de la machine : c'est le seul format qui se lit
    # directement en tableau numpy sans avoir a remettre les canaux d'aplomb.
    rgba_image = image.convertToFormat(QImage.Format.Format_RGBA8888)
    stride = rgba_image.bytesPerLine()
    buf = rgba_image.bits()
    buf.setsize(stride * rows)
    array = np.frombuffer(bytes(buf), dtype=np.uint8).reshape(rows, stride)
    return array[:, :cols * 4].reshape(rows, cols, 4).copy()


def flatten(base_rgb, layers_rgba):
    """Aplatit des calques RVBA sur un fond RVB, du dessous vers le dessus.

    layers_rgba est une liste de (image RVBA, opacite de 0 a 1), rangee du
    dessous vers le dessus - l'ordre du dessin, donc l'inverse de celui de la
    legende. La composition se fait canal par canal en flottants : passer par
    des entiers arrondirait a chaque calque, ce qui se voit des le troisieme.
    """
    import numpy as np

    result = np.asarray(base_rgb, dtype=np.float32)
    for image, opacity in layers_rgba:
        if image is None:
            continue
        image = np.asarray(image, dtype=np.float32)
        alpha = (image[..., 3:4] / 255.0) * float(opacity)
        result = image[..., :3] * alpha + result * (1.0 - alpha)
    return np.clip(result, 0, 255).astype(np.uint8)


def legend_items(layer):
    """Couples (couleur hexa, libelle) du rendu categorise d'une couche.

    Reprend la legende telle qu'elle est deja construite dans le projet (BD
    Foret, RPG, bio, Corine categorise pareil dans fetch_corine_layer) plutot
    que d'en reconstituer une : c'est la meme source que celle qui colore la
    texture, la legende ne peut donc pas s'en ecarter.

    Renvoie une liste vide si le rendu n'est pas categorise (rien a montrer
    plutot qu'une erreur).
    """
    renderer = layer.renderer() if layer is not None else None
    if renderer is None or not hasattr(renderer, "categories"):
        return []
    items = []
    for category in renderer.categories():
        symbol = category.symbol()
        if symbol is None:
            continue
        items.append((symbol.color().name(), category.label()))
    return items


ORTHO_LAYER = "ORTHOIMAGERY.ORTHOPHOTOS"
ORTHO_CAPABILITIES = (
    "https://data.geopf.fr/wmts"
    "?SERVICE=WMTS&VERSION=1.0.0&REQUEST=GetCapabilities"
)


def fetch_ortho_layer():
    """Orthophotographie IGN (BD ORTHO), en couche WMTS de la Geoplateforme.

    WMTS plutot que WMS, comme le fond Plan IGN du rapport (report/layout) :
    c'est le mode d'acces officiel du service, et celui qui passe sur les
    postes au reseau filtre. Rien n'est telecharge ici - les tuiles le sont
    au rendu, sur la seule emprise du relief (render_layer_texture), et la
    reprojection du Web Mercator vers le Lambert 93 est faite par QGIS.

    Renvoie None si la couche n'a pas pu s'ouvrir (service injoignable).
    """
    import urllib.parse

    from qgis.core import QgsRasterLayer

    uri = (
        "contextualWMSLegend=0&crs=EPSG:3857&dpiMode=7&format=image/jpeg"
        "&layers={0}&styles=normal&tileMatrixSet=PM&url={1}"
    ).format(ORTHO_LAYER, urllib.parse.quote(ORTHO_CAPABILITIES, safe=""))
    layer = QgsRasterLayer(uri, "Orthophoto IGN (habillage)", "wms")
    return layer if layer.isValid() else None


def _clc_field(name):
    if _MODERN_FIELDS:
        return QgsField(name, S, "", 3, 0)
    return QgsField(name, S, len=3, prec=0)   # pragma: no cover - QGIS anciens


def fetch_corine_layer(bbox, progress=None):
    """Telecharge Corine Land Cover sur l'emprise, en couche memoire coloree
    par grand type d'occupation du sol.

    bbox est un quadruplet (xmin, ymin, xmax, ymax) en Lambert 93 - a prendre
    ici bien plus petit que celui du bassin complet, puisqu'il ne sert qu'a
    habiller le relief conserve pour l'apercu 3D.

    Peut lever les memes erreurs que les autres appels WFS du plugin (reseau
    hydrographique, delai depasse...). Renvoie None si l'emprise ne recoupe
    aucun polygone.
    """
    if progress:
        progress("Corine Land Cover (habillage 3D)...")

    fields = QgsFields()
    fields.append(_clc_field("code"))
    fields.append(_clc_field("niveau1"))

    layer = QgsVectorLayer(
        "Polygon?crs=EPSG:2154", "Corine Land Cover (habillage)", "memory"
    )
    provider = layer.dataProvider()
    provider.addAttributes(fields)
    layer.updateFields()

    found = False
    for page in wfs_pages(LAYER_CLC, bbox=bbox, timeout=90):
        batch = []
        for record in page:
            geometry = QgsGeometry(
                QgsJsonUtils.geometryFromGeoJson(
                    json.dumps(record["geometry"])
                )
            )
            if geometry.isEmpty():
                continue
            code = str(record["properties"].get("code_18") or "").strip()
            feature = QgsFeature(fields)
            feature.setGeometry(geometry)
            feature.setAttributes([code, code[:1]])
            batch.append(feature)
        if batch:
            provider.addFeatures(batch)
            found = True
    if not found:
        return None
    layer.updateExtents()

    categories = []
    for code, label in CLC_LEVEL1.items():
        symbol = QgsFillSymbol.createSimple({
            "color": CLC_LEVEL1_COLORS.get(code, "#7f8c8d"),
            "outline_style": "no",
        })
        categories.append(QgsRendererCategory(code, symbol, label))
    layer.setRenderer(QgsCategorizedSymbolRenderer("niveau1", categories))
    return layer
