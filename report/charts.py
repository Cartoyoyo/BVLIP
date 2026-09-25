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


# Eclairage et nuancier par defaut du bloc-diagramme : soleil au nord-ouest,
# a mi-hauteur - la convention des cartes ombrees, celle qui fait lire les
# cretes en relief et non en creux. La vue 3D laisse regler les trois.
LIGHT_AZIMUTH = 315.0
LIGHT_ALTITUDE = 55.0
RELIEF_CMAP = "terrain"


def masked_relief(relief, step=1):
    """Grille d'altitudes decoupee sur le bassin, et ses coordonnees.

    Renvoie (grid, x, y), grid portant des NaN hors du bassin, ou None si
    rien n'est dessinable. Partage entre le bloc-diagramme et les exports 3D
    (report/export3d.py) : la decoupe doit etre la meme partout, sans quoi
    l'export ne montrerait pas ce que montre l'apercu.

    Hors du bassin, pas de terrain : le bloc s'arrete a la ligne de partage
    des eaux, qui est le sujet. Le test d'appartenance se fait d'un coup sur
    toutes les mailles, ce qui coute quelques centiemes de seconde.

    Le masque est ensuite dilate d'une maille : plot_surface efface tout
    quadrilatere dont un seul coin est a NaN, si bien qu'un masque colle au
    contour laisse un rebord de mailles manquantes tout autour du bassin -
    visible surtout sur la grille allegee de la vue interactive. La marge
    gardee autour du bassin (MARGIN_SHARE) porte deja de vraies altitudes
    sur cette maille de plus ; le trait du contour, pose par dessus,
    recouvre le leger debord que cela cree.
    """
    from matplotlib.path import Path

    import numpy as np

    step = max(1, int(step))
    grid = np.asarray(relief["grid"], dtype=float)[::step, ::step]
    x = np.asarray(relief["x"], dtype=float)[::step]
    y = np.asarray(relief["y"], dtype=float)[::step]
    if grid.size == 0 or x.size < 2 or y.size < 2:
        return None
    contour = relief.get("contour") or []
    if len(contour) > 2:
        mesh_x, mesh_y = np.meshgrid(x, y)
        inside = Path(contour).contains_points(
            np.column_stack((mesh_x.ravel(), mesh_y.ravel()))
        ).reshape(grid.shape)
        grid = np.where(_dilate(inside), grid, np.nan)
    if not np.isfinite(grid).any():
        return None
    return grid, x, y


def shade_relief(grid, exaggeration, texture=None,
                 light_azimuth=LIGHT_AZIMUTH, light_altitude=LIGHT_ALTITUDE,
                 cmap=RELIEF_CMAP, spacing=1.0):
    """Image RVB ombree (flottants 0-1) d'une grille d'altitudes.

    L'ombrage porte le relief bien mieux que la seule couleur : deux
    versants de meme altitude ne se distinguent que par la lumiere. Un
    habillage fourni (occupation du sol...) reprend le meme ombrage,
    applique cette fois a ses propres couleurs plutot qu'a un nuancier
    hypsometrique - shade_rgb est l'outil matplotlib prevu pour ca.

    spacing est le pas de la grille, en mailles du relief d'origine : une
    grille surechantillonnee pour l'export (pas de 1/4) doit s'ombrer avec
    les memes pentes que la grille d'origine, sans quoi elle paraitrait
    quatre fois plus plate.
    """
    from matplotlib.colors import LightSource

    import numpy as np

    low = float(np.nanmin(grid))
    high = float(np.nanmax(grid))
    filled = np.nan_to_num(grid, nan=low)
    light = LightSource(azdeg=light_azimuth, altdeg=light_altitude)
    if texture is not None:
        rgb = np.asarray(texture, dtype=float)[..., :3]
        if rgb.max() > 1.0:
            rgb = rgb / 255.0
        shaded = light.shade_rgb(
            rgb, filled, vert_exag=exaggeration, blend_mode="soft",
            dx=spacing, dy=spacing,
        )
    else:
        shaded = light.shade(
            filled, cmap=plt_cm(cmap), vert_exag=exaggeration,
            blend_mode="soft", vmin=low, vmax=high, dx=spacing, dy=spacing,
        )
    return np.clip(np.asarray(shaded)[..., :3], 0.0, 1.0)


def relief_figure(relief, figure, elevation=42.0, azimuth=-125.0,
                  exaggeration=2.2, decimate=1, texture=None,
                  show_contour=True, show_network=True, show_outlet=True,
                  show_title=True, light_azimuth=LIGHT_AZIMUTH,
                  light_altitude=LIGHT_ALTITUDE, cmap=RELIEF_CMAP,
                  coarse_decimate=None):
    """Dessine le bloc-diagramme du bassin dans la figure fournie.

    La figure est passee plutot que creee ici : le rapport en veut une hors
    ecran, la fenetre d'apercu une attachee a un canevas Qt. Le dessin, lui,
    doit rester le meme des deux cotes - c'est tout l'interet.

    decimate allege la grille d'un facteur donne : le rendu est quadratique,
    et les deux usages n'ont pas le meme besoin - voir RELIEF_DECIMATE_REPORT
    et RELIEF_DECIMATE_LIVE.

    coarse_decimate, s'il est plus grossier que decimate, pose en plus une
    seconde surface allegee, masquee au depart. La vue interactive la montre
    a la place de la surface fine le temps d'une rotation a la souris, puis
    revient a la fine au relachement : la definition choisie ne se paie plus
    a chaque mouvement, seulement a l'arret. Les deux surfaces sont rendues
    dans axes.bvlip_surfaces (fine, grossiere ou None).

    L'exageration verticale est assumee : a l'echelle reelle, un bassin de
    vingt kilometres pour mille metres de denivelee est une galette, et le
    relief qu'on cherche a montrer ne se voit pas. Le facteur est indique sur
    la figure, faute de quoi elle mentirait.

    texture, si fourni, est un habillage RVB (occupation du sol, BD Foret...)
    a la resolution pleine de relief["grid"] - donc avant decimate, qui lui
    est applique en meme temps qu'a la grille pour rester aligne. Sans lui,
    le bloc-diagramme garde son ombrage hypsometrique, au nuancier cmap.

    show_contour efface le trait rouge de la ligne de partage des eaux. Vu de
    dessus, il montre le contour du bassin ; vu de biais, il se pose parfois
    en l'air au-dessus du relief exagere et brouille plus qu'il n'aide -
    l'apercu interactif le desactive donc par defaut hors de la vue du
    dessus. show_network, show_outlet et show_title font de meme pour le
    chevelu, l'exutoire et le titre.
    """
    if not available() or not relief:
        return None
    from matplotlib import cm  # noqa: F401 - charge les nuanciers

    import numpy as np

    step = max(1, int(decimate))
    masked = masked_relief(relief, step)
    if masked is None:
        return None
    grid, x, y = masked
    if texture is not None:
        texture = np.asarray(texture)[::step, ::step]
        if texture.shape[:2] != grid.shape:
            texture = None    # desalignement inattendu : retombe sur l'ombrage
    mesh_x, mesh_y = np.meshgrid(x, y)

    low = float(np.nanmin(grid))
    high = float(np.nanmax(grid))
    axes = figure.add_subplot(111, projection="3d")
    # Le tri en profondeur de matplotlib travaille objet par objet, pas face
    # par face : la surface, d'un seul tenant, passe souvent entiere devant
    # le chevelu et l'efface. Les traits sont donc poses au-dessus d'office
    # (zorder), le decollement (lift) evitant qu'ils paraissent flotter.
    axes.computed_zorder = False

    shaded = shade_relief(
        grid, exaggeration, texture=texture, light_azimuth=light_azimuth,
        light_altitude=light_altitude, cmap=cmap,
    )
    shaded = np.dstack([shaded, np.where(np.isfinite(grid), 1.0, 0.0)])

    fine = axes.plot_surface(
        mesh_x, mesh_y, grid, facecolors=shaded, rstride=1, cstride=1,
        linewidth=0, antialiased=False, shade=False,
    )
    coarse = None
    if coarse_decimate:
        stride = int(round(float(coarse_decimate) / step))
        if stride > 1:
            coarse = axes.plot_surface(
                mesh_x, mesh_y, grid, facecolors=shaded, rstride=stride,
                cstride=stride, linewidth=0, antialiased=False, shade=False,
            )
            coarse.set_visible(False)
    axes.bvlip_surfaces = (fine, coarse)

    span = max(x.max() - x.min(), y.max() - y.min())
    # set_box_aspect etire l'axe Z d'un facteur exaggeration : un lift en
    # metres reels se retrouve donc lui aussi etire d'autant a l'affichage.
    # On le divise par l'exageration pour que le trait garde le meme
    # decollement visuel quel que soit le curseur - sans quoi il semble
    # decoller du relief a mesure qu'on exagere le relief.
    lift = 0.012 * span / exaggeration

    # Epaisseur du trait selon l'ordre de Strahler : le collecteur principal
    # ressort du chevelu au lieu de s'y noyer dans un trait uniforme.
    if show_network:
        orders = relief.get("reseau_ordre") or []
        widths = [stream_width(order) for order in orders] or None
        _drape(axes, relief.get("reseau"), x, y, grid, lift, BLEU, 0.9,
               widths=widths)
    if show_contour:
        _drape(axes, [relief.get("contour") or []], x, y, grid, lift * 1.4,
               "#c0392b", 1.2, closed=True)

    outlet = relief.get("exutoire")
    if outlet and show_outlet:
        z = _sample(x, y, grid, [outlet])[0]
        if z is not None:
            axes.scatter([outlet[0]], [outlet[1]], [z + lift * 2],
                         marker="*", s=70, color="#c0392b",
                         edgecolors="white", linewidths=0.5, depthshade=False,
                         zorder=4)

    axes.set_box_aspect((x.max() - x.min(), y.max() - y.min(),
                         (high - low) * exaggeration))
    axes.view_init(elev=elevation, azim=azimuth)
    axes.set_axis_off()
    if show_title:
        axes.set_title(
            "Relief du bassin — {0:.0f} à {1:.0f} m NGF, "
            "relief exagéré {2:.1f}×".format(low, high, exaggeration),
            fontsize=7.5, color=ARDOISE, pad=2,
        )
    figure.subplots_adjust(left=0, right=1, bottom=0,
                           top=0.94 if show_title else 1.0)
    return axes


def stream_width(order):
    """Epaisseur de trait d'un troncon selon son ordre de Strahler."""
    return min(0.6 + 0.4 * (order or 1), 2.6)


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
