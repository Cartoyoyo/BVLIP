# -*- coding: utf-8 -*-
"""Graphiques du rapport, produits avec matplotlib.

matplotlib est livre avec l'installation Windows de QGIS et present dans la
plupart des installations Linux et macOS, mais ce n'est pas une garantie. Son
absence ne doit pas priver l'utilisateur de son rapport : chaque fonction
renvoie None plutot que de lever, et la mise en page se contente alors du
tableau de valeurs.
"""

import os

# Palette commune aux graphiques et a la symbologie des couches.
BLEU = "#2980b9"
BLEU_CLAIR = "#a9cce3"
ARDOISE = "#2c3e50"
GRIS = "#7f8c8d"

# Couleurs des niveaux 1 de Corine Land Cover, dans l'esprit du referentiel :
# rouge pour l'artificialise, jaune pour l'agricole, vert pour le naturel.
#
# La correspondance se fait sur le code, jamais sur le libelle : une simple
# difference d'accentuation entre les deux modules suffirait a faire retomber
# toutes les classes sur la couleur par defaut.
CLC_COLORS = {
    "1": "#c0392b",
    "2": "#e6b422",
    "3": "#27ae60",
    "4": "#8e44ad",
    "5": "#2980b9",
}

DPI = 200


def available():
    """matplotlib est-il utilisable dans cette installation ?"""
    try:
        import matplotlib  # noqa: F401
        return True
    except ImportError:
        return False


def _figure(width_cm, height_cm):
    """Prepare une figure sans dependre du backend graphique de la machine.

    L'appel a matplotlib.use('Agg') doit preceder l'import de pyplot : QGIS
    charge deja Qt, et laisser matplotlib choisir un backend interactif ouvre
    des fenetres parasites.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure = plt.figure(figsize=(width_cm / 2.54, height_cm / 2.54))
    return plt, figure


def hypsometric_curve(hypsometry, output_path, width_cm=9.0, height_cm=6.5):
    """Courbe hypsometrique : altitude en ordonnee, part de surface au-dessus
    de cette altitude en abscisse.

    Renvoie le chemin du fichier, ou None si matplotlib manque.
    """
    if not available() or not hypsometry:
        return None
    plt, figure = _figure(width_cm, height_cm)

    points = sorted(hypsometry, key=lambda p: p["part_surface_pct"])
    shares = [p["part_surface_pct"] for p in points]
    altitudes = [p["altitude_m"] for p in points]

    axes = figure.add_subplot(111)
    axes.plot(shares, altitudes, color=BLEU, linewidth=1.8)
    axes.fill_between(shares, altitudes, min(altitudes), color=BLEU_CLAIR,
                      alpha=0.55)
    axes.set_xlabel("Part de la surface située au-dessus (%)", fontsize=8)
    axes.set_ylabel("Altitude (m NGF)", fontsize=8)
    axes.set_xlim(0, 100)
    axes.tick_params(labelsize=7)
    axes.grid(True, linewidth=0.4, color="#d5d8dc")
    for side in ("top", "right"):
        axes.spines[side].set_visible(False)
    figure.tight_layout(pad=0.6)
    figure.savefig(output_path, dpi=DPI, facecolor="white")
    plt.close(figure)
    return output_path if os.path.exists(output_path) else None


def land_cover_pie(groups, output_path, width_cm=9.0, height_cm=6.5):
    """Repartition de l'occupation du sol par niveau 1 de Corine Land Cover.

    Les classes sous 1 % sont regroupees : en dessous, l'etiquette est
    illisible et la part n'a pas de sens a cette echelle de donnee.
    """
    if not available() or not groups:
        return None
    plt, figure = _figure(width_cm, height_cm)

    retained = [g for g in groups if g["part_pct"] >= 1.0]
    residue = sum(g["part_pct"] for g in groups if g["part_pct"] < 1.0)
    labels = [g["libelle"] for g in retained]
    values = [g["part_pct"] for g in retained]
    colors = [CLC_COLORS.get(str(g.get("code")), GRIS) for g in retained]
    if residue > 0.05:
        labels.append("Autres")
        values.append(residue)
        colors.append(GRIS)

    axes = figure.add_subplot(111)
    wedges, _texts, autotexts = axes.pie(
        values, colors=colors, startangle=90, counterclock=False,
        autopct="%1.0f %%", pctdistance=0.72,
        wedgeprops={"linewidth": 1.0, "edgecolor": "white"},
        textprops={"fontsize": 7, "color": "white", "weight": "bold"},
    )
    for text in autotexts:
        if float(text.get_text().replace(" %", "")) < 6:
            text.set_visible(False)  # part trop etroite pour porter un chiffre
    axes.legend(wedges, labels, loc="center left", bbox_to_anchor=(0.98, 0.5),
                fontsize=6.5, frameon=False)
    axes.set_aspect("equal")
    figure.tight_layout(pad=0.4)
    figure.savefig(output_path, dpi=DPI, facecolor="white",
                   bbox_inches="tight")
    plt.close(figure)
    return output_path if os.path.exists(output_path) else None


def protected_areas(protected, output_path, width_cm=9.0, height_cm=5.0):
    """Part du bassin couverte par chaque zonage environnemental.

    Des barres horizontales et non verticales : les libelles sont longs -
    "Natura 2000 - ZSC, directive Habitats" - et se lisent a plat sans avoir
    a les incliner. Les zonages absents du bassin ne sont pas traces, une
    barre de longueur nulle n'apprenant rien.

    Le total est marque d'un trait vertical et non d'une barre de plus : il ne
    se compare pas aux autres, c'est l'union des surfaces et non leur somme.
    """
    if not available() or not protected:
        return None
    couples = [(z["libelle"], z["part_pct"])
               for z in protected.get("zonages") or []
               if z.get("part_pct")]
    if not couples:
        return None
    couples.reverse()   # matplotlib trace de bas en haut

    plt, figure = _figure(width_cm, height_cm)
    axes = figure.add_subplot(111)
    labels = [c[0] for c in couples]
    values = [c[1] for c in couples]
    bars = axes.barh(labels, values, color=BLEU, height=0.6)
    for bar, value in zip(bars, values):
        axes.text(value, bar.get_y() + bar.get_height() / 2,
                  " {0:.1f} %".format(value), ha="left", va="center",
                  fontsize=7, color=ARDOISE)

    total = protected.get("total_pct")
    if total:
        axes.axvline(total, color="#c0392b", linewidth=1.0, linestyle="--",
                     label="total sans double compte")
        # La legende passe sous l'axe et non dans le graphique : posee a
        # l'interieur, elle vient se coucher sur la barre la plus longue,
        # qui est justement celle qui touche le trait du total.
        axes.legend(fontsize=6.5, frameon=False, loc="upper center",
                    bbox_to_anchor=(0.5, -0.22))

    axes.set_xlabel("% de la surface du bassin", fontsize=8)
    axes.tick_params(labelsize=6.5)
    axes.set_xlim(0, max(max(values), total or 0) * 1.28)
    axes.grid(True, axis="x", linewidth=0.4, color="#d5d8dc")
    axes.set_axisbelow(True)
    for side in ("top", "right"):
        axes.spines[side].set_visible(False)
    figure.tight_layout(pad=0.5)
    figure.savefig(output_path, dpi=DPI, facecolor="white")
    plt.close(figure)
    return output_path if os.path.exists(output_path) else None


def relief_figure(relief, figure, elevation=42.0, azimuth=-125.0,
                  exaggeration=2.2, decimate=1, texture=None,
                  show_contour=True):
    """Dessine le bloc-diagramme du bassin dans la figure fournie.

    La figure est passee plutot que creee ici : le rapport en veut une hors
    ecran, la fenetre d'apercu une attachee a un canevas Qt. Le dessin, lui,
    doit rester le meme des deux cotes - c'est tout l'interet.

    decimate allege la grille d'un facteur donne : le rendu est quadratique,
    et les deux usages n'ont pas le meme besoin - voir RELIEF_DECIMATE_REPORT
    et RELIEF_DECIMATE_LIVE.

    L'exageration verticale est assumee : a l'echelle reelle, un bassin de
    vingt kilometres pour mille metres de denivelee est une galette, et le
    relief qu'on cherche a montrer ne se voit pas. Le facteur est indique sur
    la figure, faute de quoi elle mentirait.

    texture, si fourni, est un habillage RVB (occupation du sol, BD Foret...)
    a la resolution pleine de relief["grid"] - donc avant decimate, qui lui
    est applique en meme temps qu'a la grille pour rester aligne. Sans lui,
    le bloc-diagramme garde son ombrage hypsometrique par defaut.

    show_contour efface le trait rouge de la ligne de partage des eaux. Vu de
    dessus, il montre le contour du bassin ; vu de biais, il se pose parfois
    en l'air au-dessus du relief exagere et brouille plus qu'il n'aide -
    l'apercu interactif le desactive donc hors de la vue du dessus.
    """
    if not available() or not relief:
        return None
    from matplotlib import cm  # noqa: F401 - charge les nuanciers
    from matplotlib.colors import LightSource
    from matplotlib.path import Path

    import numpy as np

    step = max(1, int(decimate))
    grid = np.asarray(relief["grid"])[::step, ::step]
    x = np.asarray(relief["x"])[::step]
    y = np.asarray(relief["y"])[::step]
    if grid.size == 0 or x.size < 2 or y.size < 2:
        return None
    if texture is not None:
        texture = np.asarray(texture)[::step, ::step]
        if texture.shape[:2] != grid.shape:
            texture = None    # desalignement inattendu : retombe sur l'ombrage
    mesh_x, mesh_y = np.meshgrid(x, y)

    # Hors du bassin, pas de terrain : le bloc s'arrete a la ligne de partage
    # des eaux, qui est le sujet. Le test d'appartenance se fait d'un coup sur
    # toutes les mailles, ce qui coute quelques centiemes de seconde.
    #
    # Le masque est ensuite dilate d'une maille : plot_surface efface tout
    # quadrilatere dont un seul coin est a NaN, si bien qu'un masque colle au
    # contour laisse un rebord de mailles manquantes tout autour du bassin -
    # visible surtout sur la grille allegee de la vue interactive. La marge
    # gardee autour du bassin (MARGIN_SHARE) porte deja de vraies altitudes
    # sur cette maille de plus ; le trait du contour, pose par dessus,
    # recouvre le leger debord que cela cree.
    contour = relief.get("contour") or []
    if len(contour) > 2:
        inside = Path(contour).contains_points(
            np.column_stack((mesh_x.ravel(), mesh_y.ravel()))
        ).reshape(grid.shape)
        grid = np.where(_dilate(inside), grid, np.nan)
    if not np.isfinite(grid).any():
        return None

    low = float(np.nanmin(grid))
    high = float(np.nanmax(grid))
    axes = figure.add_subplot(111, projection="3d")

    # L'ombrage porte le relief bien mieux que la seule couleur : deux
    # versants de meme altitude ne se distinguent que par la lumiere. Un
    # habillage fourni (occupation du sol...) reprend le meme ombrage,
    # applique cette fois a ses propres couleurs plutot qu'a un nuancier
    # hypsometrique - shade_rgb est l'outil matplotlib prevu pour ca.
    light = LightSource(azdeg=315, altdeg=55)
    filled = np.nan_to_num(grid, nan=low)
    if texture is not None:
        rgb = texture.astype(float)
        if rgb.max() > 1.0:
            rgb = rgb / 255.0
        shaded = light.shade_rgb(
            rgb, filled, vert_exag=exaggeration, blend_mode="soft",
        )
        shaded = np.dstack([shaded, np.ones(grid.shape)])
    else:
        shaded = light.shade(
            filled, cmap=plt_cm("terrain"), vert_exag=exaggeration,
            blend_mode="soft", vmin=low, vmax=high,
        )
    shaded[..., 3] = np.where(np.isfinite(grid), 1.0, 0.0)

    axes.plot_surface(
        mesh_x, mesh_y, grid, facecolors=shaded, rstride=1, cstride=1,
        linewidth=0, antialiased=False, shade=False,
    )

    span = max(x.max() - x.min(), y.max() - y.min())
    # set_box_aspect etire l'axe Z d'un facteur exaggeration : un lift en
    # metres reels se retrouve donc lui aussi etire d'autant a l'affichage.
    # On le divise par l'exageration pour que le trait garde le meme
    # decollement visuel quel que soit le curseur - sans quoi il semble
    # decoller du relief a mesure qu'on exagere le relief.
    lift = 0.012 * span / exaggeration

    # Epaisseur du trait selon l'ordre de Strahler : le collecteur principal
    # ressort du chevelu au lieu de s'y noyer dans un trait uniforme.
    orders = relief.get("reseau_ordre") or []
    widths = [min(0.6 + 0.4 * order, 2.6) for order in orders] or None
    _drape(axes, relief.get("reseau"), x, y, grid, lift, BLEU, 0.9,
           widths=widths)
    if show_contour:
        _drape(axes, [contour], x, y, grid, lift * 1.4, "#c0392b", 1.2,
               closed=True)

    outlet = relief.get("exutoire")
    if outlet:
        z = _sample(x, y, grid, [outlet])[0]
        if z is not None:
            axes.scatter([outlet[0]], [outlet[1]], [z + lift * 2],
                         marker="*", s=70, color="#c0392b",
                         edgecolors="white", linewidths=0.5, depthshade=False)

    axes.set_box_aspect((x.max() - x.min(), y.max() - y.min(),
                         (high - low) * exaggeration))
    axes.view_init(elev=elevation, azim=azimuth)
    axes.set_axis_off()
    axes.set_title(
        "Relief du bassin — {0:.0f} à {1:.0f} m NGF, "
        "relief exagéré {2:.1f}×".format(low, high, exaggeration),
        fontsize=7.5, color=ARDOISE, pad=2,
    )
    figure.subplots_adjust(left=0, right=1, bottom=0, top=0.94)
    return axes


def relief_mesh_glb(relief, exaggeration=2.2, decimate=1, texture=None):
    """Bloc-diagramme en maillage texture, au format glTF binaire (.glb).

    Reprend exactement les donnees et le masque du bloc-diagramme matplotlib
    - meme ombrage, meme decoupe sur le bassin - pour que l'export corresponde
    a ce que montre l'apercu : la texture posee sur le maillage est l'image
    d'ombrage elle-meme, pas une couleur plate.

    texture, si fourni, est un habillage RVB (occupation du sol, BD Foret...)
    a la resolution pleine de relief["grid"] : c'est alors lui, ombre par le
    relief, qui devient la texture exportee - voir relief_figure.

    L'exageration verticale est appliquee directement aux altitudes (et non
    laissee a la mise a l'echelle de l'outil qui rouvre le fichier) : c'est
    la meme logique que l'export image, ce qu'on voit dans l'apercu est ce
    qu'on exporte.

    Aucune dependance nouvelle : le PNG de texture et le conteneur .glb sont
    ecrits a la main (zlib et struct, tous deux dans la bibliotheque
    standard) plutot que d'ajouter Pillow ou une lib glTF pour un unique
    export.

    Renvoie les octets du fichier .glb, ou None si les donnees manquent.
    """
    if not available() or not relief:
        return None
    from matplotlib.colors import LightSource
    from matplotlib.path import Path
    import numpy as np

    step = max(1, int(decimate))
    grid = np.asarray(relief["grid"])[::step, ::step]
    x = np.asarray(relief["x"])[::step]
    y = np.asarray(relief["y"])[::step]
    if grid.size == 0 or x.size < 2 or y.size < 2:
        return None
    if texture is not None:
        texture = np.asarray(texture)[::step, ::step]
        if texture.shape[:2] != grid.shape:
            texture = None
    mesh_x, mesh_y = np.meshgrid(x, y)

    contour = relief.get("contour") or []
    if len(contour) > 2:
        inside = Path(contour).contains_points(
            np.column_stack((mesh_x.ravel(), mesh_y.ravel()))
        ).reshape(grid.shape)
        grid = np.where(_dilate(inside), grid, np.nan)
    if not np.isfinite(grid).any():
        return None

    low = float(np.nanmin(grid))
    high = float(np.nanmax(grid))
    filled = np.nan_to_num(grid, nan=low)

    light = LightSource(azdeg=315, altdeg=55)
    if texture is not None:
        rgb_in = texture.astype(float)
        if rgb_in.max() > 1.0:
            rgb_in = rgb_in / 255.0
        shaded = light.shade_rgb(
            rgb_in, filled, vert_exag=exaggeration, blend_mode="soft",
        )
    else:
        shaded = light.shade(
            filled, cmap=plt_cm("terrain"), vert_exag=exaggeration,
            blend_mode="soft", vmin=low, vmax=high,
        )
    rgb = (np.clip(shaded[..., :3], 0.0, 1.0) * 255).astype(np.uint8)
    png_bytes = _encode_png(rgb)

    rows, cols = grid.shape
    # Recentrage sur le bassin : les coordonnees Lambert 93 valent plusieurs
    # centaines de milliers de metres, ce que Blender digere mal en simple
    # precision (le maillage se met a trembler). L'origine locale evite ca.
    cx = (x.min() + x.max()) / 2.0
    cy = (y.min() + y.max()) / 2.0

    # Convention glTF : Y vers le haut. Le nord (y croissant du terrain) est
    # pose sur -Z pour garder un repere direct standard ; une orientation
    # d'ensemble se corrige d'une simple rotation dans Blender si besoin.
    xs = (mesh_x - cx).astype(np.float32)
    ys = ((filled - low) * exaggeration).astype(np.float32)
    zs = -(mesh_y - cy).astype(np.float32)
    positions = np.stack([xs, ys, zs], axis=-1).reshape(-1, 3)

    # UV : glTF place (0,0) en haut a gauche de l'image, comme notre PNG (sa
    # ligne 0 est deja le nord) - u suit x, v suit directement l'indice de
    # ligne, sans inversion a faire.
    u = (x - x.min()) / max(x.max() - x.min(), 1e-9)
    v = (y.max() - y) / max(y.max() - y.min(), 1e-9)
    uu, vv = np.meshgrid(u, v)
    uvs = np.stack([uu, vv], axis=-1).astype(np.float32).reshape(-1, 2)

    # Un quadrilatere dont un seul coin sort du bassin ne donne aucune face :
    # meme regle de decoupe que le bloc-diagramme matplotlib.
    finite = np.isfinite(grid)
    quads_ok = finite[:-1, :-1] & finite[:-1, 1:] & finite[1:, :-1] & finite[1:, 1:]
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

    return _pack_glb(positions, uvs, indices, png_bytes)


def _encode_png(rgb):
    """Encode un tableau RVB uint8 (lignes, colonnes, 3) en PNG, sans Pillow.

    zlib (bibliotheque standard) fait la compression ; il ne reste qu'a poser
    les trois chunks obligatoires. Ecrire ces quelques lignes evite une
    dependance de plus pour ce seul export.
    """
    import struct
    import zlib

    height, width = rgb.shape[0], rgb.shape[1]
    raw = bytearray()
    for row in range(height):
        raw.append(0)                      # filtre "None" pour la ligne
        raw.extend(rgb[row].tobytes())
    compressed = zlib.compress(bytes(raw), 6)

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff))

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (signature + chunk(b"IHDR", ihdr) + chunk(b"IDAT", compressed)
            + chunk(b"IEND", b""))


def _pack_glb(positions, uvs, indices, png_bytes):
    """Assemble positions, UV, indices et texture en un fichier .glb.

    Format binaire glTF 2.0 : un en-tete, un chunk JSON qui decrit la scene,
    un chunk binaire qui porte les octets bruts (sommets, indices, image).
    """
    import json
    import struct

    def pad4(data, fill=b"\x00"):
        remainder = len(data) % 4
        return data if remainder == 0 else data + fill * (4 - remainder)

    parts = [
        positions.astype("<f4").tobytes(),
        uvs.astype("<f4").tobytes(),
        indices.astype("<u4").tobytes(),
        png_bytes,
    ]
    buffer_views = []
    blob = bytearray()
    for part in parts:
        part = pad4(part)
        buffer_views.append((len(blob), len(part)))
        blob += part

    pos_min = positions.min(axis=0).tolist()
    pos_max = positions.max(axis=0).tolist()

    gltf = {
        "asset": {"version": "2.0", "generator": "BVLIP"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{
            "primitives": [{
                "attributes": {"POSITION": 0, "TEXCOORD_0": 1},
                "indices": 2,
                "material": 0,
            }],
        }],
        "materials": [{
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
        "images": [{"mimeType": "image/png", "bufferView": 3}],
        "buffers": [{"byteLength": len(blob)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": buffer_views[0][0],
             "byteLength": buffer_views[0][1], "target": 34962},
            {"buffer": 0, "byteOffset": buffer_views[1][0],
             "byteLength": buffer_views[1][1], "target": 34962},
            {"buffer": 0, "byteOffset": buffer_views[2][0],
             "byteLength": buffer_views[2][1], "target": 34963},
            {"buffer": 0, "byteOffset": buffer_views[3][0],
             "byteLength": buffer_views[3][1]},
        ],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": len(positions),
             "type": "VEC3", "min": pos_min, "max": pos_max},
            {"bufferView": 1, "componentType": 5126, "count": len(uvs),
             "type": "VEC2"},
            {"bufferView": 2, "componentType": 5125, "count": len(indices),
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


def plt_cm(name):
    """Nuancier matplotlib, quelle que soit la version.

    matplotlib 3.9 a retire matplotlib.cm.get_cmap ; matplotlib.colormaps
    n'existe pas avant 3.5. On prend ce qui est la.
    """
    import matplotlib
    try:
        return matplotlib.colormaps[name]
    except (AttributeError, KeyError):      # pragma: no cover - anciens
        from matplotlib import cm
        return cm.get_cmap(name)


def _dilate(mask):
    """Etend un masque booleen d'une maille dans les huit directions.

    Pas de scipy ici : la grille du bloc-diagramme reste petite (quelques
    centaines de mailles de cote au pire), un decalage de tableau numpy fait
    l'affaire sans nouvelle dependance.
    """
    import numpy as np

    padded = np.pad(mask, 1, mode="constant", constant_values=False)
    grown = padded[1:-1, 1:-1].copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            grown |= padded[1 + dy:padded.shape[0] - 1 + dy,
                            1 + dx:padded.shape[1] - 1 + dx]
    return grown


def _sample(x, y, grid, points):
    """Altitude de la grille sous chaque point, ou None hors du bassin."""
    import numpy as np

    heights = []
    for px, py in points:
        col = int(np.clip(np.searchsorted(x, px) - 1, 0, grid.shape[1] - 1))
        # y decroit du nord au sud : la recherche se fait sur son inverse.
        row = int(np.clip(np.searchsorted(-y, -py) - 1, 0, grid.shape[0] - 1))
        value = grid[row, col]
        heights.append(None if not np.isfinite(value) else float(value))
    return heights


def _drape(axes, lines, x, y, grid, lift, color, width, closed=False,
           widths=None):
    """Pose une ligne sur la surface, en suivant les altitudes.

    Les points tombant hors du bassin sont coupes : le trait s'interrompt au
    lieu de plonger a zero, ce qui dessinerait une falaise qui n'existe pas.

    widths, si fourni, donne une epaisseur par ligne (meme longueur que
    lines) au lieu de l'epaisseur unique width - c'est ainsi que le reseau
    hydrographique varie selon l'ordre de Strahler du troncon.
    """
    import numpy as np

    for index, line in enumerate(lines or []):
        if not line or len(line) < 2:
            continue
        line_width = widths[index] if widths is not None else width
        points = list(line) + ([line[0]] if closed else [])
        heights = _sample(x, y, grid, points)
        segment = []
        for (px, py), z in zip(points, heights):
            if z is None:
                if len(segment) > 1:
                    _plot(axes, segment, lift, color, line_width)
                segment = []
                continue
            segment.append((px, py, z))
        if len(segment) > 1:
            _plot(axes, segment, lift, color, line_width)


def _plot(axes, segment, lift, color, width):
    xs = [p[0] for p in segment]
    ys = [p[1] for p in segment]
    zs = [p[2] + lift for p in segment]
    axes.plot(xs, ys, zs, color=color, linewidth=width, solid_capstyle="round")


# Allegement de la grille au dessin, et non au stockage : la grille
# conservee sert aussi bien l'image du rapport que la vue interactive, qui
# n'ont pas les memes besoins.
#
# Le cout du rendu est quadratique, mesure sur une grille de 400 mailles de
# cote : 17,9 s telle quelle, 5,1 s a une maille sur deux, 2,4 s a une sur
# trois - pour des images qu'on ne distingue pas a 9 cm de large, ou une
# maille sur deux fait deja trois pixels et demi.
#
# Le rapport prend donc une maille sur deux. La vue interactive va bien plus
# bas : elle redessine la surface entiere a chaque mouvement de souris, et
# c'est le temps d'une image qui decide si la rotation est agreable ou non.
RELIEF_DECIMATE_REPORT = 2
RELIEF_DECIMATE_LIVE = 5

# Budget de mailles vise pour une rotation fluide, tire du meme banc de
# mesure : une maille sur cinq sur la plus grande grille geree (400x400)
# tombe autour de ce compte. RELIEF_DECIMATE_LIVE reste le plafond de secours
# pour cette meme grande grille - live_decimate() ne l'adoucit qu'en dessous.
LIVE_CELL_BUDGET = 6500


def live_decimate(relief):
    """Choisit le plus petit pas de decimation qui tient le budget interactif.

    RELIEF_DECIMATE_LIVE etait fixe, calibre sur la plus grande grille geree
    (400 mailles de cote, le plafond MAX_CELLS de relief.py). La plupart des
    bassins produisent une grille bien plus petite, ou ce meme pas allege
    inutilement le relief. Ici, le pas s'adapte a la grille reellement recue :
    un petit bassin gagne une vue interactive nettement plus nette, un grand
    bassin retrouve exactement le comportement d'avant.
    """
    grid = relief.get("grid") if relief else None
    if grid is None:
        return RELIEF_DECIMATE_LIVE
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    for step in range(1, RELIEF_DECIMATE_LIVE + 1):
        if -(-rows // step) * -(-cols // step) <= LIVE_CELL_BUDGET:
            return step
    return RELIEF_DECIMATE_LIVE


def relief_block(relief, output_path, width_cm=9.0, height_cm=7.0,
                 decimate=RELIEF_DECIMATE_REPORT):
    """Bloc-diagramme du bassin, en image, pour le rapport."""
    if not available() or not relief:
        return None
    plt, figure = _figure(width_cm, height_cm)
    if relief_figure(relief, figure, decimate=decimate) is None:
        plt.close(figure)
        return None
    figure.savefig(output_path, dpi=DPI, facecolor="white")
    plt.close(figure)
    return output_path if os.path.exists(output_path) else None


def build_all(metrics_values, land_cover, folder, relief=None,
              protected=None):
    """Produit les quatre graphiques dans le dossier donne.

    Renvoie un dictionnaire {cle: chemin ou None}.
    """
    os.makedirs(folder, exist_ok=True)
    metrics_values = metrics_values or {}
    corine = (land_cover or {}).get("corine") or {}
    return {
        "relief": relief_block(
            relief, os.path.join(folder, "relief.png"),
        ),
        "hypsometrie": hypsometric_curve(
            metrics_values.get("hypsometrie"),
            os.path.join(folder, "hypsometrie.png"),
        ),
        "occupation": land_cover_pie(
            corine.get("niveaux1"),
            os.path.join(folder, "occupation.png"),
        ),
        "zonages": protected_areas(
            protected, os.path.join(folder, "zonages.png"),
        ),
    }
