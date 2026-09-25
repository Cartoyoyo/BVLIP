# -*- coding: utf-8 -*-
"""Exports 3D du bloc-diagramme : maillage .glb et page HTML autonome.

Les deux exports partagent la meme texture, bien plus fine que la grille
d'altitudes : la grille est plafonnee a 400 mailles de cote (MAX_CELLS dans
core/relief.py), ce qui suffit a porter le relief mais donne une image floue
une fois posee sur un ecran entier ou rendue dans Blender. La texture est
donc refaite a une definition de l'ordre de 2 000 pixels - l'habillage
re-rendu par QGIS a cette definition, l'ombrage recalcule sur une grille
d'altitudes interpolee - et le chevelu, la ligne de crete et l'exutoire y
sont peints directement. Dans le fichier exporte, ils ne sont pas des objets
a part : ils collent au relief quel que soit l'outil qui le rouvre, sans
jamais flotter au-dessus comme les traits de l'apercu matplotlib.

Rien a installer : le conteneur .glb s'ecrit avec struct, les images
s'encodent par QImage (Qt est la, puisqu'on est dans QGIS), et la page HTML
embarque sa propre visionneuse WebGL de quelques dizaines de lignes plutot
qu'une bibliotheque - elle s'ouvre donc sans reseau, dans n'importe quel
navigateur, chez quelqu'un qui n'a pas QGIS.
"""

import base64
import json

from . import charts

# Definition visee pour le grand cote de la texture : 2 048 pixels passent
# sur toutes les cartes graphiques, y compris integrees, et restent nets en
# plein ecran. Le facteur est borne pour qu'une toute petite grille ne
# produise pas une image gigantesque de pixels interpoles.
TEXTURE_TARGET = 2048
TEXTURE_FACTOR_MAX = 8

# Couleurs des traits peints sur la texture : les memes que dans l'apercu.
STREAM_COLOR = charts.BLEU
CREST_COLOR = "#c0392b"


# ---------------------------------------------------------------- Texture

def texture_factor(relief):
    """Facteur de surechantillonnage de la texture pour cette grille."""
    grid = relief.get("grid") if relief else None
    if grid is None or not len(grid):
        return 1
    longest = max(len(grid), len(grid[0]))
    return max(1, min(TEXTURE_FACTOR_MAX,
                      int(round(TEXTURE_TARGET / float(longest)))))


def fine_axes(x, y, factor):
    """Centres de pixel de la texture fine, en Lambert 93.

    La texture couvre la meme emprise que la grille, bords de maille
    compris : chaque maille d'origine se decoupe en factor x factor pixels.
    Ce sont ces centres qu'il faut passer au rendu QGIS de l'habillage
    (core/drape.py) pour qu'il tombe pile sur la texture.
    """
    import numpy as np

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    dx = (x[-1] - x[0]) / (len(x) - 1)
    dy = (y[0] - y[-1]) / (len(y) - 1)
    xs = x[0] - dx / 2.0 + (np.arange(len(x) * factor) + 0.5) * dx / factor
    ys = y[0] + dy / 2.0 - (np.arange(len(y) * factor) + 0.5) * dy / factor
    return xs, ys


def _upsample(grid, factor):
    """Interpolation bilineaire d'une grille pleine (sans NaN)."""
    import numpy as np

    rows, cols = grid.shape

    def positions(count):
        pos = (np.arange(count * factor) + 0.5) / factor - 0.5
        pos = np.clip(pos, 0, count - 1)
        first = np.floor(pos).astype(int)
        second = np.minimum(first + 1, count - 1)
        return first, second, pos - first

    r0, r1, fr = positions(rows)
    c0, c1, fc = positions(cols)
    fr = fr[:, None]
    fc = fc[None, :]
    top = grid[r0][:, c0] * (1 - fc) + grid[r0][:, c1] * fc
    bottom = grid[r1][:, c0] * (1 - fc) + grid[r1][:, c1] * fc
    return top * (1 - fr) + bottom * fr


def fine_texture(relief, exaggeration, factor, base_rgb=None,
                 light_azimuth=charts.LIGHT_AZIMUTH,
                 light_altitude=charts.LIGHT_ALTITUDE, cmap=charts.RELIEF_CMAP,
                 show_network=True, show_outlet=True, show_contour=False):
    """Texture RVB (uint8) du bloc-diagramme, factor fois plus fine.

    base_rgb est l'habillage compose a cette meme definition (voir
    fine_axes), ou None pour l'ombrage hypsometrique. Renvoie None si le
    relief n'est pas dessinable.
    """
    import numpy as np

    masked = charts.masked_relief(relief)
    if masked is None:
        return None
    grid, x, y = masked
    low = float(np.nanmin(grid))
    filled = np.nan_to_num(grid, nan=low)
    fine = _upsample(filled, factor) if factor > 1 else filled
    if base_rgb is not None and np.asarray(base_rgb).shape[:2] != fine.shape:
        base_rgb = None
    shaded = charts.shade_relief(
        fine, exaggeration, texture=base_rgb, light_azimuth=light_azimuth,
        light_altitude=light_altitude, cmap=cmap, spacing=1.0 / factor,
    )
    rgb = (shaded * 255.0 + 0.5).astype(np.uint8)
    return _paint_overlays(rgb, relief, x, y, show_network, show_outlet,
                           show_contour)


def _paint_overlays(rgb, relief, x, y, show_network, show_outlet,
                    show_contour):
    """Peint chevelu, ligne de crete et exutoire sur la texture.

    QPainter plutot qu'un trace a la main : il lisse les traits, et une
    texture qu'on regarde de pres dans Blender montre le moindre escalier.
    L'epaisseur suit la definition de l'image, pour que le trait garde la
    meme presence relative quelle que soit la taille du bassin.
    """
    import numpy as np
    from qgis.PyQt.QtGui import QImage

    lines = (relief.get("reseau") or []) if show_network else []
    contour = (relief.get("contour") or []) if show_contour else []
    outlet = relief.get("exutoire") if show_outlet else None
    if not lines and len(contour) < 3 and not outlet:
        return rgb

    height, width = rgb.shape[:2]
    rgb = np.ascontiguousarray(rgb)
    image = QImage(rgb.tobytes(), width, height, 3 * width,
                   QImage.Format.Format_RGB888).copy()
    _draw_overlays(image, relief, x, y, lines, contour, outlet)

    image = image.convertToFormat(QImage.Format.Format_RGB888)
    stride = image.bytesPerLine()
    buf = image.bits()
    buf.setsize(stride * height)
    array = np.frombuffer(bytes(buf), dtype=np.uint8).reshape(height, stride)
    return array[:, :width * 3].reshape(height, width, 3).copy()


def overlay_rgba(relief, x, y, shape, which):
    """Calque RVBA transparent portant un seul trace : "reseau" (chevelu),
    "contour" (ligne de crete) ou "exutoire".

    Pour la page HTML interactive, ou chacun se coche a part : les traits
    sont peints comme sur la texture fine (_paint_overlays), mais sur fond
    transparent, et la page les pose par-dessus le relief ombre.
    Renvoie None si le relief n'a pas ce trace.
    """
    import numpy as np
    from qgis.PyQt.QtGui import QColor, QImage

    lines = (relief.get("reseau") or []) if which == "reseau" else []
    contour = (relief.get("contour") or []) if which == "contour" else []
    outlet = relief.get("exutoire") if which == "exutoire" else None
    if not lines and len(contour) < 3 and not outlet:
        return None

    height, width = shape
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(QColor(0, 0, 0, 0))
    _draw_overlays(image, relief, x, y, lines, contour, outlet)

    image = image.convertToFormat(QImage.Format.Format_RGBA8888)
    stride = image.bytesPerLine()
    buf = image.bits()
    buf.setsize(stride * height)
    array = np.frombuffer(bytes(buf), dtype=np.uint8).reshape(height, stride)
    return array[:, :width * 4].reshape(height, width, 4).copy()


def _draw_overlays(image, relief, x, y, lines, contour, outlet):
    """Peint chevelu, ligne de crete et exutoire sur une QImage, en place."""
    from qgis.PyQt.QtCore import QPointF, Qt
    from qgis.PyQt.QtGui import QBrush, QColor, QPainter, QPen, QPolygonF

    height, width = image.height(), image.width()
    dx = (x[-1] - x[0]) / (len(x) - 1)
    dy = (y[0] - y[-1]) / (len(y) - 1)
    left = x[0] - dx / 2.0
    top = y[0] + dy / 2.0
    scale_x = width / (dx * len(x))
    scale_y = height / (dy * len(y))

    def point(px, py):
        return QPointF((px - left) * scale_x, (top - py) * scale_y)

    def polygon(points):
        return QPolygonF([point(px, py) for px, py in points])

    unit = max(1.0, max(width, height) / 900.0)
    painter = QPainter(image)
    try:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        if lines:
            orders = relief.get("reseau_ordre") or []
            for index, line in enumerate(lines):
                if not line or len(line) < 2:
                    continue
                order = orders[index] if index < len(orders) else 1
                pen = QPen(QColor(STREAM_COLOR))
                pen.setWidthF(unit * 1.8 * charts.stream_width(order))
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
                painter.drawPolyline(polygon(line))
        if len(contour) > 2:
            pen = QPen(QColor(CREST_COLOR))
            pen.setWidthF(unit * 1.8)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.drawPolygon(polygon(contour))
        if outlet:
            centre = point(outlet[0], outlet[1])
            radius = unit * 5.0
            pen = QPen(QColor("white"))
            pen.setWidthF(unit * 1.2)
            painter.setPen(pen)
            painter.setBrush(QBrush(QColor(CREST_COLOR)))
            painter.drawEllipse(centre, radius, radius)
    finally:
        painter.end()


def relief_rasters(relief, exaggeration, factor,
                   light_azimuth=charts.LIGHT_AZIMUTH,
                   light_altitude=charts.LIGHT_ALTITUDE,
                   cmap=charts.RELIEF_CMAP):
    """Couleurs hypsometriques (RVB) et ombrage (niveaux de gris), separes.

    La page HTML interactive recompose elle-meme la texture : elle empile
    les habillages coches, puis applique l'ombrage en "soft light", la
    formule de matplotlib (LightSource.blend_soft_light) qu'emploie
    shade_relief. Il lui faut donc l'ombrage a part, et non deja fondu
    dans une texture. Renvoie (hypso, ombrage), ou None.
    """
    import numpy as np
    from matplotlib.colors import LightSource, Normalize

    masked = charts.masked_relief(relief)
    if masked is None:
        return None
    grid, _x, _y = masked
    low = float(np.nanmin(grid))
    high = float(np.nanmax(grid))
    filled = np.nan_to_num(grid, nan=low)
    fine = _upsample(filled, factor) if factor > 1 else filled
    light = LightSource(azdeg=light_azimuth, altdeg=light_altitude)
    intensity = light.hillshade(
        fine, vert_exag=exaggeration, dx=1.0 / factor, dy=1.0 / factor,
    )
    colors = charts.plt_cm(cmap)(Normalize(vmin=low, vmax=high)(fine))
    hypso = (np.clip(colors[..., :3], 0, 1) * 255.0 + 0.5).astype(np.uint8)
    shade = (np.clip(intensity, 0, 1) * 255.0 + 0.5).astype(np.uint8)
    return hypso, np.repeat(shade[..., None], 3, axis=2)


def encode_image(rgb, fmt="PNG", quality=-1):
    """Encode une image RVB ou RVBA uint8 en PNG ou JPEG, par Qt."""
    import numpy as np
    from qgis.PyQt.QtCore import QBuffer, QByteArray, QIODevice
    from qgis.PyQt.QtGui import QImage

    rgb = np.ascontiguousarray(rgb)
    height, width = rgb.shape[:2]
    if rgb.ndim == 3 and rgb.shape[2] == 4:
        image = QImage(rgb.tobytes(), width, height, 4 * width,
                       QImage.Format.Format_RGBA8888).copy()
    else:
        image = QImage(rgb.tobytes(), width, height, 3 * width,
                       QImage.Format.Format_RGB888).copy()
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, fmt, quality)
    buffer.close()
    return bytes(data)


# --------------------------------------------------------------- Maillage

def _mesh(relief, exaggeration):
    """Sommets, normales, UV et triangles du bassin, a pleine resolution.

    Renvoie un dictionnaire, ou None si le relief n'est pas dessinable.
    Les coordonnees sont recentrees sur le bassin : en Lambert 93 elles
    valent plusieurs centaines de milliers de metres, ce que Blender digere
    mal en simple precision (le maillage se met a trembler).

    Convention glTF : Y vers le haut. Le nord (y croissant du terrain) est
    pose sur -Z pour garder un repere direct standard.
    """
    import numpy as np

    masked = charts.masked_relief(relief)
    if masked is None:
        return None
    grid, x, y = masked
    rows, cols = grid.shape
    low = float(np.nanmin(grid))
    high = float(np.nanmax(grid))
    filled = np.nan_to_num(grid, nan=low)
    mesh_x, mesh_y = np.meshgrid(x, y)
    cx = (x.min() + x.max()) / 2.0
    cy = (y.min() + y.max()) / 2.0

    heights = (filled - low) * exaggeration
    positions = np.stack([
        (mesh_x - cx), heights, -(mesh_y - cy),
    ], axis=-1).astype(np.float32).reshape(-1, 3)

    # Normales lissees, tirees des pentes de la grille : sans elles, les
    # visionneuses glTF calculent une normale par face et le relief sort
    # facette comme un modele de jeu video des annees 1990. Surface
    # Y = h(X, Z) avec Z = -y : la normale vaut (-dh/dX, 1, -dh/dZ), soit
    # (-dh/dx, 1, dh/dy).
    slope_x = np.gradient(heights, x, axis=1)
    slope_y = np.gradient(heights, y, axis=0)
    normals = np.stack([-slope_x, np.ones_like(heights), slope_y], axis=-1)
    normals /= np.linalg.norm(normals, axis=-1, keepdims=True)
    normals = normals.astype(np.float32).reshape(-1, 3)

    # UV : la texture couvre les mailles bords compris (voir fine_axes), le
    # centre de la maille (r, c) tombe donc en ((c + 0.5)/cols, (r + 0.5)/
    # rows). glTF place (0, 0) en haut a gauche de l'image, la ou est notre
    # ligne 0 - le nord : aucune inversion a faire.
    u = (np.arange(cols) + 0.5) / cols
    v = (np.arange(rows) + 0.5) / rows
    uu, vv = np.meshgrid(u, v)
    uvs = np.stack([uu, vv], axis=-1).astype(np.float32).reshape(-1, 2)

    # Un quadrilatere dont un seul coin sort du bassin ne donne aucune face :
    # meme regle de decoupe que le bloc-diagramme matplotlib.
    finite = np.isfinite(grid)
    quads_ok = (finite[:-1, :-1] & finite[:-1, 1:]
                & finite[1:, :-1] & finite[1:, 1:])
    rr, cc = np.nonzero(quads_ok)
    if rr.size == 0:
        return None
    i00 = rr * cols + cc
    i01 = i00 + 1
    i10 = i00 + cols
    i11 = i10 + 1
    indices = np.empty(rr.size * 6, dtype=np.uint32)
    indices[0::6] = i00
    indices[1::6] = i10
    indices[2::6] = i01
    indices[3::6] = i01
    indices[4::6] = i10
    indices[5::6] = i11

    return {
        "positions": positions, "normals": normals, "uvs": uvs,
        "indices": indices, "origin": (cx, cy, low), "low": low,
        "high": high, "grid": grid, "x": x, "y": y,
    }


def glb_bytes(relief, exaggeration, texture_rgb):
    """Bloc-diagramme en maillage texture, au format glTF binaire (.glb).

    L'exageration verticale est appliquee directement aux altitudes (et non
    laissee a la mise a l'echelle de l'outil qui rouvre le fichier) : ce
    qu'on voit dans l'apercu est ce qu'on exporte.

    L'origine Lambert 93 du recentrage, l'exageration et le systeme de
    coordonnees sont ranges dans les extras du noeud : Blender les montre
    comme proprietes personnalisees, de quoi replacer le modele sur la carte
    sans avoir a les retrouver.

    Renvoie les octets du fichier, ou None si les donnees manquent.
    """
    mesh = _mesh(relief, exaggeration)
    if mesh is None or texture_rgb is None:
        return None
    png = encode_image(texture_rgb, "PNG")
    origin = mesh["origin"]
    extras = {
        "crs": "EPSG:2154",
        "origin_x": round(origin[0], 3),
        "origin_y": round(origin[1], 3),
        "origin_z": round(origin[2], 3),
        "vertical_exaggeration": round(float(exaggeration), 3),
        "axes": "X = est, Y = altitude, -Z = nord",
    }
    return _pack_glb(mesh["positions"], mesh["normals"], mesh["uvs"],
                     mesh["indices"], png, extras)


def _pack_glb(positions, normals, uvs, indices, png_bytes, extras):
    """Assemble sommets, normales, UV, indices et texture en un .glb.

    Format binaire glTF 2.0 : un en-tete, un chunk JSON qui decrit la scene,
    un chunk binaire qui porte les octets bruts (sommets, indices, image).
    """
    import struct

    def pad4(data, fill=b"\x00"):
        remainder = len(data) % 4
        return data if remainder == 0 else data + fill * (4 - remainder)

    parts = [
        positions.astype("<f4").tobytes(),
        normals.astype("<f4").tobytes(),
        uvs.astype("<f4").tobytes(),
        indices.astype("<u4").tobytes(),
        png_bytes,
    ]
    views = []
    blob = bytearray()
    for part in parts:
        part = pad4(part)
        views.append((len(blob), len(part)))
        blob += part

    def view(index, target=None):
        entry = {"buffer": 0, "byteOffset": views[index][0],
                 "byteLength": views[index][1]}
        if target:
            entry["target"] = target
        return entry

    gltf = {
        "asset": {"version": "2.0", "generator": "BVLIP"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "Bassin versant", "extras": extras}],
        "meshes": [{
            "name": "Bassin versant",
            "primitives": [{
                "attributes": {"POSITION": 0, "NORMAL": 1, "TEXCOORD_0": 2},
                "indices": 3,
                "material": 0,
            }],
        }],
        "materials": [{
            "name": "Relief",
            "pbrMetallicRoughness": {
                "baseColorTexture": {"index": 0},
                "metallicFactor": 0.0,
                "roughnessFactor": 0.9,
            },
            "doubleSided": True,
        }],
        "textures": [{"source": 0, "sampler": 0}],
        "samplers": [{"magFilter": 9729, "minFilter": 9987,
                      "wrapS": 33071, "wrapT": 33071}],
        "images": [{"mimeType": "image/png", "bufferView": 4}],
        "buffers": [{"byteLength": len(blob)}],
        "bufferViews": [
            view(0, 34962), view(1, 34962), view(2, 34962), view(3, 34963),
            view(4),
        ],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": len(positions),
             "type": "VEC3", "min": positions.min(axis=0).tolist(),
             "max": positions.max(axis=0).tolist()},
            {"bufferView": 1, "componentType": 5126, "count": len(normals),
             "type": "VEC3"},
            {"bufferView": 2, "componentType": 5126, "count": len(uvs),
             "type": "VEC2"},
            {"bufferView": 3, "componentType": 5125, "count": len(indices),
             "type": "SCALAR"},
        ],
    }

    json_bytes = pad4(
        json.dumps(gltf, separators=(",", ":")).encode("utf-8"), fill=b" "
    )
    bin_bytes = pad4(bytes(blob))
    header = struct.pack(
        "<4sII", b"glTF", 2, 12 + 8 + len(json_bytes) + 8 + len(bin_bytes)
    )
    json_chunk = struct.pack("<I4s", len(json_bytes), b"JSON") + json_bytes
    bin_chunk = struct.pack("<I4s", len(bin_bytes), b"BIN\x00") + bin_bytes
    return header + json_chunk + bin_chunk


# ------------------------------------------------------------ Page HTML

def _b64(data):
    return base64.b64encode(data).decode("ascii")


def _layer_image(rgba):
    """(base64, type MIME) d'un calque : JPEG s'il est plein, PNG sinon.

    Une orthophoto n'a pas de transparence et pese cinq fois moins en JPEG ;
    un habillage vectoriel (Corine, BD Foret) garde ses trous en PNG, ou ses
    aplats se compressent de toute facon tres bien.
    """
    import numpy as np

    rgba = np.asarray(rgba)
    if rgba.shape[2] == 4 and int(rgba[..., 3].min()) < 255:
        return _b64(encode_image(rgba, "PNG")), "image/png"
    return _b64(encode_image(rgba[..., :3], "JPG", 88)), "image/jpeg"


def interactive_data(hypso, shade, layers, overlays, grey, ui):
    """Donnees de la page interactive, pretes pour html_page(interactive=).

    layers : dicts {key, label, rgba (ou None pour le relief gris),
    checked, opacity (0-100), legend [(couleur, libelle)...]}, dans l'ordre
    de la pile (le premier est dessus). overlays : dicts {key, label, rgba,
    checked}. ui : libelles traduits du panneau.
    """
    out_layers = []
    for layer in layers:
        entry = {
            "key": layer["key"], "label": layer["label"],
            "checked": bool(layer["checked"]),
            "opacity": int(layer["opacity"]),
            "legend": [[color, label] for color, label in layer["legend"]],
        }
        if layer.get("rgba") is not None:
            entry["img"], entry["mime"] = _layer_image(layer["rgba"])
        out_layers.append(entry)
    out_overlays = []
    for overlay in overlays:
        if overlay.get("rgba") is None:
            continue
        img, mime = _layer_image(overlay["rgba"])
        out_overlays.append({"key": overlay["key"], "label": overlay["label"],
                             "checked": bool(overlay["checked"]),
                             "img": img, "mime": mime})
    return {
        "hypso": _b64(encode_image(hypso, "JPG", 90)),
        "shade": _b64(encode_image(shade, "JPG", 92)),
        "layers": out_layers, "overlays": out_overlays,
        "grey": int(grey), "ui": ui,
    }


def html_page(relief, exaggeration, texture_rgb, texts, legend=None,
              interactive=None):
    """Page HTML autonome : le bassin en 3D, a tourner dans un navigateur.

    La page n'embarque que les altitudes brutes (un flottant par maille) et
    la texture en JPEG : le maillage se reconstruit dans le navigateur, ce
    qui divise le poids du fichier par cinq environ par rapport a un
    maillage tout fait. L'exageration reste donc reglable dans la page.

    texts porte les libelles deja traduits (title, subtitle, hint, reset,
    exaggeration, nowebgl, legend) ; legend est une liste de (titre,
    [(couleur, libelle), ...]) pour les habillages actifs.

    interactive (voir interactive_data) remplace texture_rgb et legend : la
    page recoit alors chaque habillage a part, l'ombrage et les traces, et
    un panneau pour les empiler comme dans la fenetre 3D de QGIS. Sans lui,
    la page n'affiche que la texture fournie, sans panneau - c'est la vue
    embarquee dans la fenetre 3D, que le panneau Qt pilote.

    Renvoie le texte de la page, ou None si le relief n'est pas dessinable.
    """
    import numpy as np

    masked = charts.masked_relief(relief)
    if masked is None or (texture_rgb is None and interactive is None):
        return None
    grid, x, y = masked
    rows, cols = grid.shape
    low = float(np.nanmin(grid))
    high = float(np.nanmax(grid))
    heights = (grid - low).astype("<f4")      # NaN hors du bassin

    data = {
        "rows": rows, "cols": cols,
        "dx": float(abs(x[1] - x[0])), "dy": float(abs(y[0] - y[1])),
        "low": low, "high": high, "exag": float(exaggeration),
        "heights": base64.b64encode(heights.tobytes()).decode("ascii"),
    }
    if interactive is not None:
        data.update(interactive)
        legend = None                 # construite par la page, a la volee
    else:
        data["texture"] = _b64(encode_image(texture_rgb, "JPG", 90))

    legend_html = ""
    for title, items in legend or []:
        rows_html = "".join(
            '<li><i style="background:{0}"></i>{1}</li>'.format(
                _escape(color), _escape(label))
            for color, label in items
        )
        legend_html += "<h3>{0}</h3><ul>{1}</ul>".format(
            _escape(title), rows_html)
    if legend_html:
        legend_html = '<aside id="legend"><h2>{0}</h2>{1}</aside>'.format(
            _escape(texts["legend"]), legend_html)

    page = _HTML_TEMPLATE
    replacements = {
        "@@TITLE@@": _escape(texts["title"]),
        "@@SUBTITLE@@": _escape(texts["subtitle"]),
        "@@HINT@@": _escape(texts["hint"]),
        "@@RESET@@": _escape(texts["reset"]),
        "@@EXAG_LABEL@@": _escape(texts["exaggeration"]),
        "@@NOWEBGL@@": json.dumps(texts["nowebgl"]),
        "@@LEGEND@@": legend_html,
        "@@DATA@@": json.dumps(data, separators=(",", ":")),
    }
    for key, value in replacements.items():
        page = page.replace(key, value)
    return page


def _escape(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


# Visionneuse WebGL 1 ecrite a la main : un maillage texture, une camera en
# orbite, la souris et le tactile. WebGL 1 et evenements souris/tactiles
# plutot que WebGL 2 et "pointer*" : la meme page s'affiche dans un
# navigateur et dans l'onglet web de la fenetre 3D, dont le moteur (QtWebKit,
# sous QGIS 3 en Qt5) ne connait ni l'un ni l'autre. Pas de three.js : il faudrait soit un
# acces reseau a l'ouverture, soit embarquer 600 Ko de bibliotheque pour
# n'en utiliser qu'une fraction.
_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>@@TITLE@@</title>
<style>
  html, body { margin: 0; height: 100%; overflow: hidden;
    font: 14px/1.4 "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: #eef1f4; color: #2c3e50; }
  canvas { display: block; width: 100%; height: 100%; cursor: grab;
    touch-action: none; }
  canvas:active { cursor: grabbing; }
  header { position: absolute; top: 12px; left: 16px; right: 16px;
    pointer-events: none; }
  header h1 { margin: 0; font-size: 18px; }
  header p { margin: 2px 0 0; font-size: 13px; color: #5d6d7e; }
  #controls { position: absolute; bottom: 16px; left: 16px;
    display: flex; align-items: center; flex-wrap: wrap;
    background: rgba(255,255,255,.9); padding: 8px 12px; border-radius: 8px;
    box-shadow: 0 1px 4px rgba(0,0,0,.15); }
  #controls > * { margin: 2px 6px; }
  #controls button { font: inherit; padding: 4px 10px; border-radius: 6px;
    border: 1px solid #aab7c4; background: #fff; cursor: pointer; }
  #controls button:hover { background: #eaf2f8; }
  #hint { font-size: 12px; color: #5d6d7e; }
  #compass { position: absolute; top: 12px; right: 16px; width: 48px;
    height: 48px; border-radius: 50%; background: rgba(255,255,255,.9);
    box-shadow: 0 1px 4px rgba(0,0,0,.15); }
  #compass svg { width: 100%; height: 100%; }
  #legend { position: absolute; top: 72px; right: 16px; max-height: 60%;
    overflow: auto; background: rgba(255,255,255,.9); padding: 8px 12px;
    border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,.15);
    max-width: 240px; font-size: 12px; }
  #legend h2 { margin: 0 0 4px; font-size: 13px; }
  #legend h3 { margin: 6px 0 2px; font-size: 12px; }
  #legend ul { list-style: none; margin: 0; padding: 0; }
  #legend li { display: flex; align-items: center; }
  #legend li i { margin-right: 6px; }
  #legend i { width: 12px; height: 12px; flex: none;
    border: 1px solid #888; }
  #error { position: absolute; top: 0; right: 0; bottom: 0; left: 0;
    display: none;
    align-items: center; justify-content: center; font-size: 16px; }
  @media (max-width: 600px) {
    #legend { display: none; }
    #hint { display: none; }
  }
  /* Page interactive : panneau de reglages a droite, comme dans QGIS. */
  #stage { position: absolute; top: 0; left: 0; right: 0; bottom: 0; }
  body.with-panel #stage { right: 280px; }
  body.with-panel #legend { left: 16px; right: auto; }
  #panel { display: none; position: absolute; top: 0; right: 0; bottom: 0;
    width: 280px; box-sizing: border-box; overflow-y: auto;
    background: #f7f9fb; border-left: 1px solid #d5dde5;
    padding: 10px 12px; font-size: 13px; }
  body.with-panel #panel { display: block; }
  #panel section { border: 1px solid #d5dde5; border-radius: 8px;
    background: #fff; margin: 0 0 10px; padding: 6px 10px 10px; }
  #panel h4 { margin: 0 0 6px; font-size: 13px; color: #34495e; }
  #panel .row { display: flex; align-items: center; margin: 3px 0; }
  #panel .row > * { margin: 0 2px; }
  #panel .row button { flex: 1; }
  #panel .row .spacer { flex: 1; visibility: hidden; }
  #panel button { font: inherit; font-size: 12px; padding: 4px 4px;
    border-radius: 6px; border: 1px solid #aab7c4; background: #fff;
    cursor: pointer; }
  #panel button:hover { background: #eaf2f8; }
  #panel button:disabled { color: #aab7c4; cursor: default;
    background: #f4f6f7; }
  #panel input[type=range] { width: 100%; }
  #panel ul { list-style: none; margin: 0 0 4px; padding: 0;
    border: 1px solid #d5dde5; border-radius: 6px; max-height: 190px;
    overflow-y: auto; }
  #panel li { display: flex; align-items: center; padding: 3px 6px;
    cursor: pointer; }
  #panel li input { margin: 0 6px 0 0; }
  #panel li.sel { background: #d6eaf8; }
  #panel label.check { display: flex; align-items: center; margin: 2px 0; }
  #panel label.check input { margin: 0 6px 0 0; }
  #panel .value { min-width: 40px; text-align: right; color: #5d6d7e; }
  #panelToggle { display: none; position: absolute; top: 72px; right: 16px;
    font: inherit; font-size: 12px; padding: 4px 10px; border-radius: 6px;
    border: 1px solid #aab7c4; background: rgba(255,255,255,.9);
    cursor: pointer; box-shadow: 0 1px 4px rgba(0,0,0,.15); }
  body.interactive #panelToggle { display: block; }
  @media (max-width: 760px) {
    body.with-panel #stage { right: 0; }
    #panel { width: 88%; box-shadow: -2px 0 8px rgba(0,0,0,.2); }
  }
</style>
</head>
<body>
<div id="stage">
<canvas id="view"></canvas>
<header><h1>@@TITLE@@</h1><p>@@SUBTITLE@@</p></header>
<div id="compass" title="N"><svg viewBox="-24 -24 48 48">
  <g id="needle"><path d="M0,-17 L6,4 L0,0 L-6,4 Z" fill="#c0392b"/>
  <path d="M0,17 L6,4 L0,0 L-6,4 Z" fill="#aab7c4"/>
  <text x="0" y="-18" text-anchor="middle" font-size="9"
    font-weight="bold" fill="#2c3e50">N</text></g></svg></div>
@@LEGEND@@
<div id="controls">
  <button id="reset">@@RESET@@</button>
  <label>@@EXAG_LABEL@@
    <input id="exag" type="range" min="1" max="10" step="0.1"></label>
  <span id="exagValue"></span>
  <span id="hint">@@HINT@@</span>
</div>
<button id="panelToggle"></button>
<div id="error"></div>
</div>
<div id="panel"></div>
<script>
// Tout dans une fonction : le moteur de QGIS (QtWebKit) refuse une
// constante globale qui porte le nom d'un id de la page (exagValue...).
(function () {
"use strict";
const D = @@DATA@@;

function bytes(b64) {
  const s = atob(b64), out = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) out[i] = s.charCodeAt(i);
  return out;
}

// --- Matrices 4x4, rangees par colonnes comme WebGL les attend.
function perspective(fovy, aspect, near, far) {
  const f = 1 / Math.tan(fovy / 2), nf = 1 / (near - far);
  return [f / aspect, 0, 0, 0, 0, f, 0, 0, 0, 0, (far + near) * nf, -1,
          0, 0, 2 * far * near * nf, 0];
}
function lookAt(e, t, u) {
  let zx = e[0] - t[0], zy = e[1] - t[1], zz = e[2] - t[2];
  let l = Math.hypot(zx, zy, zz); zx /= l; zy /= l; zz /= l;
  let xx = u[1] * zz - u[2] * zy, xy = u[2] * zx - u[0] * zz,
      xz = u[0] * zy - u[1] * zx;
  l = Math.hypot(xx, xy, xz); xx /= l; xy /= l; xz /= l;
  const yx = zy * xz - zz * xy, yy = zz * xx - zx * xz, yz = zx * xy - zy * xx;
  return [xx, yx, zx, 0, xy, yy, zy, 0, xz, yz, zz, 0,
    -(xx * e[0] + xy * e[1] + xz * e[2]),
    -(yx * e[0] + yy * e[1] + yz * e[2]),
    -(zx * e[0] + zy * e[1] + zz * e[2]), 1];
}
function multiply(a, b) {
  const o = new Array(16);
  for (let c = 0; c < 4; c++)
    for (let r = 0; r < 4; r++) {
      let s = 0;
      for (let k = 0; k < 4; k++) s += a[k * 4 + r] * b[c * 4 + k];
      o[c * 4 + r] = s;
    }
  return o;
}

const canvas = document.getElementById("view");
// preserveDrawingBuffer : sans lui, l'image n'est plus lisible une fois
// affichee, et le bouton "Image PNG" recopierait un canevas vide.
const glOptions = { antialias: true, preserveDrawingBuffer: true };
const gl = canvas.getContext("webgl", glOptions) ||
           canvas.getContext("experimental-webgl", glOptions);
if (!gl) {
  const box = document.getElementById("error");
  box.textContent = @@NOWEBGL@@;
  box.style.display = "flex";
  throw new Error("WebGL");
}

// --- Maillage reconstruit depuis la grille d'altitudes.
// WebGL 1 n'indexe qu'en 16 bits sans extension : la grille est donc coupee
// en bandes de lignes de moins de 65 536 sommets, qui se recouvrent d'une
// ligne pour ne pas laisser de fente entre elles.
const R = D.rows, C = D.cols;
const H = new Float32Array(bytes(D.heights).buffer);
const bandRows = Math.max(2, Math.floor(65535 / C));
const bands = [];
for (let r0 = 0; r0 < R - 1; r0 += bandRows - 1) {
  const r1 = Math.min(R, r0 + bandRows), n = (r1 - r0) * C;
  const pos = new Float32Array(n * 3), uv = new Float32Array(n * 2);
  for (let r = r0; r < r1; r++)
    for (let c = 0; c < C; c++) {
      const g = r * C + c, i = (r - r0) * C + c, h = H[g];
      pos[i * 3] = (c - (C - 1) / 2) * D.dx;
      pos[i * 3 + 1] = isFinite(h) ? h : 0;
      pos[i * 3 + 2] = (r - (R - 1) / 2) * D.dy;
      uv[i * 2] = (c + 0.5) / C;
      uv[i * 2 + 1] = (r + 0.5) / R;
    }
  const tris = [], o = r0 * C;
  for (let r = r0; r < r1 - 1; r++)
    for (let c = 0; c < C - 1; c++) {
      const a = r * C + c, b = a + 1, d = a + C, e = d + 1;
      if (isFinite(H[a]) && isFinite(H[b]) && isFinite(H[d]) && isFinite(H[e]))
        tris.push(a - o, d - o, b - o, b - o, d - o, e - o);
    }
  if (tris.length) bands.push({ pos: pos, uv: uv, idx: new Uint16Array(tris) });
}

function shader(type, src) {
  const s = gl.createShader(type);
  gl.shaderSource(s, src); gl.compileShader(s);
  return s;
}
const prog = gl.createProgram();
gl.attachShader(prog, shader(gl.VERTEX_SHADER,
  "attribute vec3 p; attribute vec2 t; uniform mat4 m; uniform float ex;" +
  "varying vec2 v;" +
  "void main() { v = t; gl_Position = m * vec4(p.x, p.y * ex, p.z, 1.0); }"));
// Trois textures : la couleur (habillages empiles, ou texture toute faite),
// l'ombrage, fondu en "soft light" comme LightSource.blend_soft_light de
// matplotlib, et les traces (chevelu, crete, exutoire) poses par-dessus,
// hors ombrage. useShade et useOver a 0 : la couleur passe telle quelle.
gl.attachShader(prog, shader(gl.FRAGMENT_SHADER,
  "precision mediump float; varying vec2 v;" +
  "uniform sampler2D tc; uniform sampler2D ts; uniform sampler2D to;" +
  "uniform float useShade; uniform float useOver;" +
  "void main() {" +
  "  vec3 d = texture2D(tc, v).rgb;" +
  "  float i = texture2D(ts, v).r;" +
  "  d = mix(d, 2.0 * d * i + d * d * (1.0 - 2.0 * i), useShade);" +
  "  vec4 o = texture2D(to, v);" +
  "  gl_FragColor = vec4(mix(d, o.rgb, o.a * useOver), 1.0);" +
  "}"));
gl.linkProgram(prog);
gl.useProgram(prog);
gl.uniform1i(gl.getUniformLocation(prog, "tc"), 0);
gl.uniform1i(gl.getUniformLocation(prog, "ts"), 1);
gl.uniform1i(gl.getUniformLocation(prog, "to"), 2);
const uUseShade = gl.getUniformLocation(prog, "useShade");
const uUseOver = gl.getUniformLocation(prog, "useOver");
const locP = gl.getAttribLocation(prog, "p");
const locT = gl.getAttribLocation(prog, "t");
gl.enableVertexAttribArray(locP);
gl.enableVertexAttribArray(locT);

function buffer(target, data) {
  const buf = gl.createBuffer();
  gl.bindBuffer(target, buf);
  gl.bufferData(target, data, gl.STATIC_DRAW);
  return buf;
}
bands.forEach(function (b) {
  b.bPos = buffer(gl.ARRAY_BUFFER, b.pos);
  b.bUv = buffer(gl.ARRAY_BUFFER, b.uv);
  b.bIdx = buffer(gl.ELEMENT_ARRAY_BUFFER, b.idx);
  b.count = b.idx.length;
  b.pos = b.uv = b.idx = null;
});

// WebGL 1 ne fait de mipmaps que sur une texture de cote puissance de deux :
// l'image est reechantillonnee sur un canevas a la bonne taille avant envoi.
// Chaque image passe par un canevas 2D a cette taille, qui sert aussi a
// empiler les habillages (drawImage + globalAlpha) avant envoi a WebGL.
const CAP = Math.min(4096, gl.getParameter(gl.MAX_TEXTURE_SIZE));
let textureReady = false;
let TW = 1, TH = 1;
function pot(n) {
  let p = 1;
  while (p < n && p < CAP) p *= 2;
  return p;
}
function texture(unit) {
  const t = gl.createTexture();
  gl.activeTexture(gl.TEXTURE0 + unit);
  gl.bindTexture(gl.TEXTURE_2D, t);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA,
                gl.UNSIGNED_BYTE, new Uint8Array([255, 255, 255, 0]));
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  return t;
}
function upload(unit, tex, source) {
  gl.activeTexture(gl.TEXTURE0 + unit);
  gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, source);
  gl.generateMipmap(gl.TEXTURE_2D);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER,
                   gl.LINEAR_MIPMAP_LINEAR);
}
const texColor = texture(0), texShade = texture(1), texOver = texture(2);
function sheet() {
  const cv = document.createElement("canvas");
  cv.width = TW; cv.height = TH;
  return cv;
}
let colorSheet = null, overSheet = null;

// Charge des images base64 et rappelle done() une fois toutes pretes.
function loadImages(items, done) {
  let left = items.length;
  if (!left) { done(); return; }
  items.forEach(function (item) {
    const im = new Image();
    im.onload = im.onerror = function () {
      item.el = im.width ? im : null;
      if (--left === 0) done();
    };
    im.src = "data:" + item.mime + ";base64," + item.b64;
  });
}

const interactive = !!D.layers;
const layers = interactive ? D.layers : [];
const overlays = interactive ? D.overlays : [];
let hypsoEl = null;

function compose() {
  if (!colorSheet) return;            // images pas encore chargees
  const ctx = colorSheet.getContext("2d");
  ctx.globalAlpha = 1;
  const active = layers.filter(function (l) { return l.checked; });
  if (!active.length) {
    // Aucun habillage : le nuancier hypsometrique, comme dans QGIS.
    ctx.drawImage(hypsoEl, 0, 0, TW, TH);
  } else {
    // Fond blanc, ou gris si le relief gris est tout en bas de la pile :
    // meme regle que la fenetre 3D (_current_texture).
    const bottom = active[active.length - 1];
    const greyBase = bottom.key === "relief_gris";
    const grey = "rgb(" + D.grey + "," + D.grey + "," + D.grey + ")";
    ctx.fillStyle = greyBase ? grey : "#fff";
    ctx.fillRect(0, 0, TW, TH);
    for (let i = layers.length - 1; i >= 0; i--) {
      const l = layers[i];
      if (!l.checked || (greyBase && l === bottom)) continue;
      ctx.globalAlpha = l.opacity / 100;
      if (l.key === "relief_gris") {
        ctx.fillStyle = grey;
        ctx.fillRect(0, 0, TW, TH);
      } else if (l.el) {
        ctx.drawImage(l.el, 0, 0, TW, TH);
      }
    }
    ctx.globalAlpha = 1;
  }
  upload(0, texColor, colorSheet);
  const over = overSheet.getContext("2d");
  over.clearRect(0, 0, TW, TH);
  overlays.forEach(function (o) {
    if (o.checked && o.el) over.drawImage(o.el, 0, 0, TW, TH);
  });
  upload(2, texOver, overSheet);
  updateLegend();
  draw();
}

if (interactive) {
  const items = [{ b64: D.hypso, mime: "image/jpeg" },
                 { b64: D.shade, mime: "image/jpeg" }];
  layers.concat(overlays).forEach(function (l) {
    if (l.img) items.push({ b64: l.img, mime: l.mime, owner: l });
  });
  loadImages(items, function () {
    hypsoEl = items[0].el;
    TW = pot(hypsoEl.width); TH = pot(hypsoEl.height);
    colorSheet = sheet(); overSheet = sheet();
    items.forEach(function (it) { if (it.owner) it.owner.el = it.el; });
    const shadeSheet = sheet();
    shadeSheet.getContext("2d").drawImage(items[1].el, 0, 0, TW, TH);
    upload(1, texShade, shadeSheet);
    gl.uniform1f(uUseShade, 1);
    gl.uniform1f(uUseOver, 1);
    textureReady = true;
    compose();
  });
} else {
  const items = [{ b64: D.texture, mime: "image/jpeg" }];
  loadImages(items, function () {
    const im = items[0].el;
    TW = pot(im.width); TH = pot(im.height);
    colorSheet = sheet();
    colorSheet.getContext("2d").drawImage(im, 0, 0, TW, TH);
    upload(0, texColor, colorSheet);
    gl.uniform1f(uUseShade, 0);
    gl.uniform1f(uUseOver, 0);
    textureReady = true;
    draw();
  });
}

const uM = gl.getUniformLocation(prog, "m");
const uEx = gl.getUniformLocation(prog, "ex");
gl.enable(gl.DEPTH_TEST);
gl.clearColor(0.933, 0.945, 0.957, 1);

// --- Camera en orbite autour du centre du bassin.
// dist a 0 veut dire "a cadrer" : la distance est calculee au premier dessin,
// quand la taille du canevas est connue (voir fitDistance).
const span = Math.max(C * D.dx, R * D.dy);
const start = { yaw: -125 * Math.PI / 180, pitch: 42 * Math.PI / 180,
                dist: 0, panX: 0, panZ: 0 };
const FOV = 35 * Math.PI / 180;

function viewMatrix(c, w, h) {
  // Meme convention d'azimut que l'apercu matplotlib : l'angle se mesure
  // depuis l'est, dans le sens direct ; le nord est sur -Z.
  const target = [c.panX, (D.high - D.low) * exag / 2, c.panZ];
  const eye = [
    target[0] + c.dist * Math.cos(c.pitch) * Math.cos(c.yaw),
    target[1] + c.dist * Math.sin(c.pitch),
    target[2] - c.dist * Math.cos(c.pitch) * Math.sin(c.yaw)
  ];
  const proj = perspective(FOV, w / h, span / 500, span * 20);
  return multiply(proj, lookAt(eye, target, [0, 1, 0]));
}

// Points d'appui du cadrage : un sommet du bassin sur k, 3 000 au plus.
// Les vrais sommets plutot que le rectangle de la grille : un bassin est
// rarement rectangulaire, et cadrer sur les coins le montrerait trop petit.
const fitPts = [];
(function () {
  let n = 0;
  for (let i = 0; i < H.length; i++) if (isFinite(H[i])) n++;
  const k = Math.max(1, Math.floor(n / 3000));
  let j = 0;
  for (let r = 0; r < R; r++)
    for (let c = 0; c < C; c++) {
      const h = H[r * C + c];
      if (!isFinite(h) || (j++ % k)) continue;
      fitPts.push((c - (C - 1) / 2) * D.dx, h, (r - (R - 1) / 2) * D.dy);
    }
})();

// Plus petite distance ou tout le bassin tient a l'ecran, en laissant la
// place de l'en-tete en haut et de la barre de commandes en bas. Recherche
// par dichotomie : la projection n'a pas de forme inverse simple.
function fitDistance(w, h, dpr) {
  const top = 1 - 2 * 80 * dpr / h, bottom = -1 + 2 * 90 * dpr / h;
  const side = 0.94;
  function fits(dist) {
    const c = copy(cam);
    c.dist = dist; c.panX = c.panZ = 0;
    const m = viewMatrix(c, w, h);
    for (let i = 0; i < fitPts.length; i += 3) {
      const x = fitPts[i], y = fitPts[i + 1] * exag, z = fitPts[i + 2];
      const cw = m[3] * x + m[7] * y + m[11] * z + m[15];
      if (cw <= 0) return false;
      const nx = (m[0] * x + m[4] * y + m[8] * z + m[12]) / cw;
      const ny = (m[1] * x + m[5] * y + m[9] * z + m[13]) / cw;
      if (nx < -side || nx > side || ny < bottom || ny > top) return false;
    }
    return true;
  }
  let lo = span * 0.1, hi = span * 6;
  if (!fits(hi)) return hi;
  for (let i = 0; i < 30; i++) {
    const mid = (lo + hi) / 2;
    if (fits(mid)) hi = mid; else lo = mid;
  }
  return hi;
}
function copy(o) {
  const out = {};
  for (const k in o) out[k] = o[k];
  return out;
}
let cam = copy(start), exag = D.exag;
// Camera reprise de l'adresse (#cam=yaw,pitch,dist,panX,panZ) : la fenetre
// 3D de QGIS recharge la page quand l'habillage change, sans perdre la vue.
const saved = /cam=([^&]+)/.exec(location.hash);
if (saved) {
  const v = saved[1].split(",").map(parseFloat);
  if (v.length === 5 && v.every(isFinite))
    cam = { yaw: v[0], pitch: v[1], dist: v[2], panX: v[3], panZ: v[4] };
}
const exagInput = document.getElementById("exag");
const exagValue = document.getElementById("exagValue");
function showExag() {
  exagInput.value = exag;
  exagValue.textContent = exag.toFixed(1) + "×";
}
showExag();

let pending = false;
function draw() {
  if (pending) return;
  pending = true;
  requestAnimationFrame(function () {
    pending = false;
    const dpr = window.devicePixelRatio || 1;
    const w = Math.round(canvas.clientWidth * dpr),
          h = Math.round(canvas.clientHeight * dpr);
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w; canvas.height = h;
    }
    if (!w || !h) return;             // canevas pas encore dimensionne
    gl.viewport(0, 0, w, h);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    if (!cam.dist) cam.dist = fitDistance(w, h, dpr);
    gl.uniformMatrix4fv(uM, false, viewMatrix(cam, w, h));
    gl.uniform1f(uEx, exag);
    if (textureReady)
      bands.forEach(function (b) {
        gl.bindBuffer(gl.ARRAY_BUFFER, b.bPos);
        gl.vertexAttribPointer(locP, 3, gl.FLOAT, false, 0, 0);
        gl.bindBuffer(gl.ARRAY_BUFFER, b.bUv);
        gl.vertexAttribPointer(locT, 2, gl.FLOAT, false, 0, 0);
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, b.bIdx);
        gl.drawElements(gl.TRIANGLES, b.count, gl.UNSIGNED_SHORT, 0);
      });
    // Aiguille : le nord (-Z) projete sur l'ecran tourne avec la camera.
    const angle = cam.yaw * 180 / Math.PI + 90;
    document.getElementById("needle").setAttribute(
      "transform", "rotate(" + angle + ")");
  });
}

// --- Souris et tactile : glisser tourne, clic droit ou Maj deplace,
// molette ou pincement zoome. Evenements souris et tactiles plutot que
// "pointer*" : le moteur web de QGIS (QtWebKit) ne connait pas ces derniers.
function move(dx, dy, pan) {
  if (pan) {
    const k = cam.dist / canvas.clientHeight;
    const s = Math.sin(cam.yaw), c = Math.cos(cam.yaw);
    cam.panX += (dx * s - dy * c) * k;
    cam.panZ += (dx * c + dy * s) * k;
  } else {
    cam.yaw -= dx * 0.008;
    cam.pitch = Math.min(1.55, Math.max(0.05, cam.pitch + dy * 0.008));
  }
  draw();
}
function zoom(f) {
  cam.dist = Math.min(span * 6, Math.max(span * 0.1, cam.dist * f));
  draw();
}

let drag = null;
canvas.addEventListener("contextmenu", function (e) { e.preventDefault(); });
canvas.addEventListener("mousedown", function (e) {
  e.preventDefault();
  drag = { x: e.clientX, y: e.clientY, pan: e.button === 2 || e.shiftKey };
});
window.addEventListener("mousemove", function (e) {
  if (!drag) return;
  const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
  drag.x = e.clientX; drag.y = e.clientY;
  move(dx, dy, drag.pan);
});
window.addEventListener("mouseup", function () { drag = null; });

let touch = null;
function touchState(e) {
  const t = e.touches;
  if (t.length >= 2)
    return { pinch: Math.sqrt(Math.pow(t[0].clientX - t[1].clientX, 2) +
                              Math.pow(t[0].clientY - t[1].clientY, 2)) };
  return t.length ? { x: t[0].clientX, y: t[0].clientY } : null;
}
canvas.addEventListener("touchstart", function (e) {
  e.preventDefault(); touch = touchState(e);
});
canvas.addEventListener("touchmove", function (e) {
  e.preventDefault();
  const now = touchState(e);
  if (touch && now) {
    if (now.pinch && touch.pinch) zoom(touch.pinch / now.pinch);
    else if (!now.pinch && !touch.pinch)
      move(now.x - touch.x, now.y - touch.y, false);
  }
  touch = now;
});
canvas.addEventListener("touchend", function (e) { touch = touchState(e); });

function onWheel(e) {
  e.preventDefault();
  const delta = e.deltaY !== undefined ? e.deltaY : -e.wheelDelta;
  zoom(Math.exp(delta * 0.001));
}
if ("onwheel" in canvas) canvas.addEventListener("wheel", onWheel);
else canvas.addEventListener("mousewheel", onWheel);

exagInput.addEventListener("input", function () {
  exag = parseFloat(exagInput.value);
  showExag();
  draw();
});
document.getElementById("reset").addEventListener("click", function () {
  cam = copy(start);
  draw();
});
window.addEventListener("resize", draw);

function setView(elevation, azimuth) {
  cam.pitch = Math.min(1.55, Math.max(0.05, elevation * Math.PI / 180));
  cam.yaw = azimuth * Math.PI / 180;
  cam.panX = cam.panZ = 0;
  cam.dist = 0;                       // recadre le bassin entier
  draw();
}
function setExag(value) { exag = value; showExag(); draw(); }

// --- Pilotage depuis QGIS : la fenetre 3D du plugin appelle ces fonctions
// quand la page y est affichee (points de vue, zoom, exageration).
window.bvlip = {
  view: setView,
  zoom: function (factor) { zoom(1 / factor); },
  camera: function () {
    return [cam.yaw, cam.pitch, cam.dist, cam.panX, cam.panZ].join(",");
  },
  exaggeration: setExag
};

// --- Panneau de la page interactive : les memes reglages que la fenetre 3D
// de QGIS (vue, habillages empiles avec ordre et opacite, exageration), plus
// les traces a cocher et l'image PNG. Construit ici plutot qu'en HTML : il
// n'existe que dans la page exportee, et ses libelles viennent de D.ui.
// Tout texte venu des donnees passe par textContent, jamais innerHTML.
const VIEWS = { nw: [42, 125], top: [89, -90], ne: [42, 55],
                sw: [42, -125], se: [42, -55] };
let selected = -1;

function el(tag, attrs, text) {
  const e = document.createElement(tag);
  if (attrs) for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (text !== undefined) e.textContent = text;
  return e;
}
function btn(text, onClick, title) {
  const b = el("button", title ? { title: title } : null, text);
  b.addEventListener("click", onClick);
  return b;
}
function row(parent, children) {
  const r = el("div", { "class": "row" });
  children.forEach(function (c) { r.appendChild(c); });
  parent.appendChild(r);
  return r;
}
function section(panel, title) {
  const s = el("section");
  s.appendChild(el("h4", null, title));
  panel.appendChild(s);
  return s;
}

function updateLegend() {
  if (!interactive) return;
  let box = document.getElementById("legend");
  if (!box) {
    box = el("aside", { id: "legend" });
    document.getElementById("stage").appendChild(box);
  }
  while (box.firstChild) box.removeChild(box.firstChild);
  box.appendChild(el("h2", null, D.ui.legend));
  let any = false;
  layers.forEach(function (l) {
    if (!l.checked || !l.legend.length) return;
    any = true;
    box.appendChild(el("h3", null, l.label));
    const ul = el("ul");
    l.legend.forEach(function (item) {
      const li = el("li"), swatch = el("i");
      swatch.style.background = item[0];
      li.appendChild(swatch);
      li.appendChild(document.createTextNode(item[1]));
      ul.appendChild(li);
    });
    box.appendChild(ul);
  });
  box.style.display = any ? "" : "none";
}

function savePng() {
  const a = el("a", { download: "bassin_versant_3d.png",
                      href: canvas.toDataURL("image/png") });
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

function buildPanel() {
  const U = D.ui, panel = document.getElementById("panel");

  const view = section(panel, U.view);
  function look(name) { return function () { setView(VIEWS[name][0], VIEWS[name][1]); }; }
  row(view, [btn(U.nw, look("nw")), btn(U.top, look("top")), btn(U.ne, look("ne"))]);
  row(view, [btn(U.sw, look("sw")), el("button", { "class": "spacer" }),
             btn(U.se, look("se"))]);
  row(view, [btn(U.zoomOut, function () { zoom(1.25); }),
             btn(U.zoomIn, function () { zoom(1 / 1.25); })]);

  const lay = section(panel, U.layers);
  const list = el("ul");
  lay.appendChild(list);
  const moveRow = row(lay, []);
  const up = btn(U.up, function () { move2(-1); });
  const down = btn(U.down, function () { move2(1); });
  moveRow.appendChild(up); moveRow.appendChild(down);
  const opHead = row(lay, [el("span", null, U.opacity)]);
  const opValue = el("span", { "class": "value" }, "—");
  opHead.appendChild(el("span", { "class": "spacer" }));
  opHead.appendChild(opValue);
  const opInput = el("input", { type: "range", min: "0", max: "100",
                                step: "1" });
  lay.appendChild(opInput);
  const presets = [90, 75, 50].map(function (v) {
    return btn(v + " %", function () { setOpacity(v, true); });
  });
  row(lay, presets);

  function renderList() {
    while (list.firstChild) list.removeChild(list.firstChild);
    layers.forEach(function (l, i) {
      const li = el("li");
      if (i === selected) li.className = "sel";
      const box = el("input", { type: "checkbox" });
      box.checked = l.checked;
      box.addEventListener("click", function (e) { e.stopPropagation(); });
      box.addEventListener("change", function () {
        l.checked = box.checked;
        renderList();
        compose();
      });
      li.appendChild(box);
      li.appendChild(document.createTextNode(
        l.label + (l.checked && l.opacity < 100 ? "  (" + l.opacity + " %)" : "")));
      li.addEventListener("click", function () {
        selected = i; renderList(); syncOpacity();
      });
      list.appendChild(li);
    });
    up.disabled = selected <= 0;
    down.disabled = selected < 0 || selected >= layers.length - 1;
  }
  function syncOpacity() {
    const l = layers[selected];
    opInput.disabled = !l;
    presets.forEach(function (b) { b.disabled = !l; });
    opInput.value = l ? l.opacity : 100;
    opValue.textContent = l ? l.opacity + " %" : "—";
  }
  function setOpacity(value, redraw) {
    const l = layers[selected];
    if (!l) return;
    l.opacity = value;
    syncOpacity();
    renderList();
    if (redraw && l.checked) compose();
  }
  function move2(step) {
    const target = selected + step;
    if (selected < 0 || target < 0 || target >= layers.length) return;
    const tmp = layers[selected];
    layers[selected] = layers[target];
    layers[target] = tmp;
    selected = target;
    renderList();
    if (layers[target].checked || layers[target - step].checked) compose();
  }
  // Curseur : le libelle suit le glisser, la texture se recompose au
  // relachement - un recompose par cran figerait la page sur un grand bassin.
  opInput.addEventListener("input", function () {
    setOpacity(parseInt(opInput.value, 10), false);
  });
  opInput.addEventListener("change", function () {
    setOpacity(parseInt(opInput.value, 10), true);
  });
  layers.forEach(function (l, i) { if (selected < 0 && l.checked) selected = i; });
  renderList();
  syncOpacity();

  if (overlays.length) {
    const show = section(panel, U.display);
    overlays.forEach(function (o) {
      const label = el("label", { "class": "check" });
      const box = el("input", { type: "checkbox" });
      box.checked = o.checked;
      box.addEventListener("change", function () {
        o.checked = box.checked;
        compose();
      });
      label.appendChild(box);
      label.appendChild(document.createTextNode(o.label));
      show.appendChild(label);
    });
  }

  const ex = section(panel, U.exaggeration);
  row(ex, [1.5, 2, 2.5, 5].map(function (v) {
    return btn("×" + String(v).replace(".", U.decimal),
               function () { setExag(v); });
  }));

  const out = section(panel, U.export);
  row(out, [btn(U.png, savePng)]);

  const toggle = document.getElementById("panelToggle");
  toggle.textContent = U.settings;
  toggle.addEventListener("click", function () {
    document.body.classList.toggle("with-panel");
    draw();
  });
}

if (interactive) {
  document.body.classList.add("interactive");
  if (window.innerWidth > 760) document.body.classList.add("with-panel");
  buildPanel();
}
draw();
})();
</script>
</body>
</html>
"""
