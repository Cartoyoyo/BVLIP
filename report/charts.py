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
                  exaggeration=2.2, decimate=1):
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
    mesh_x, mesh_y = np.meshgrid(x, y)

    # Hors du bassin, pas de terrain : le bloc s'arrete a la ligne de partage
    # des eaux, qui est le sujet. Le test d'appartenance se fait d'un coup sur
    # toutes les mailles, ce qui coute quelques centiemes de seconde.
    contour = relief.get("contour") or []
    if len(contour) > 2:
        inside = Path(contour).contains_points(
            np.column_stack((mesh_x.ravel(), mesh_y.ravel()))
        ).reshape(grid.shape)
        grid = np.where(inside, grid, np.nan)
    if not np.isfinite(grid).any():
        return None

    low = float(np.nanmin(grid))
    high = float(np.nanmax(grid))
    axes = figure.add_subplot(111, projection="3d")

    # L'ombrage porte le relief bien mieux que la seule couleur : deux
    # versants de meme altitude ne se distinguent que par la lumiere.
    shaded = LightSource(azdeg=315, altdeg=55).shade(
        np.nan_to_num(grid, nan=low), cmap=plt_cm("terrain"),
        vert_exag=exaggeration, blend_mode="soft",
        vmin=low, vmax=high,
    )
    shaded[..., 3] = np.where(np.isfinite(grid), 1.0, 0.0)

    axes.plot_surface(
        mesh_x, mesh_y, grid, facecolors=shaded, rstride=1, cstride=1,
        linewidth=0, antialiased=False, shade=False,
    )

    span = max(x.max() - x.min(), y.max() - y.min())
    lift = 0.012 * span            # de quoi poser un trait sans qu'il s'enfonce
    _drape(axes, relief.get("reseau"), x, y, grid, lift, BLEU, 0.9)
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


def _drape(axes, lines, x, y, grid, lift, color, width, closed=False):
    """Pose une ligne sur la surface, en suivant les altitudes.

    Les points tombant hors du bassin sont coupes : le trait s'interrompt au
    lieu de plonger a zero, ce qui dessinerait une falaise qui n'existe pas.
    """
    import numpy as np

    for line in lines or []:
        if not line or len(line) < 2:
            continue
        points = list(line) + ([line[0]] if closed else [])
        heights = _sample(x, y, grid, points)
        segment = []
        for (px, py), z in zip(points, heights):
            if z is None:
                if len(segment) > 1:
                    _plot(axes, segment, lift, color, width)
                segment = []
                continue
            segment.append((px, py, z))
        if len(segment) > 1:
            _plot(axes, segment, lift, color, width)


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
