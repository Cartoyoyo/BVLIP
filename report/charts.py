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


def concentration_times(times, output_path, width_cm=9.0, height_cm=4.5):
    """Temps de concentration selon les quatre formules.

    Les afficher cote a cote est le propos : leur dispersion renseigne autant
    que leur valeur, et une barre isolee tres au-dessus des autres signale une
    formule employee hors de son domaine.
    """
    if not available() or not times:
        return None
    noms = [("kirpich_h", "Kirpich"), ("giandotti_h", "Giandotti"),
            ("passini_h", "Passini"), ("ventura_h", "Ventura")]
    couples = [(label, times.get(key)) for key, label in noms
               if times.get(key) is not None]
    if not couples:
        return None

    plt, figure = _figure(width_cm, height_cm)
    axes = figure.add_subplot(111)
    labels = [c[0] for c in couples]
    values = [c[1] for c in couples]
    bars = axes.bar(labels, values, color=BLEU, width=0.55)
    moyenne = times.get("moyen_h")
    if moyenne:
        axes.axhline(moyenne, color="#c0392b", linewidth=1.0,
                     linestyle="--", label="moyenne")
        axes.legend(fontsize=6.5, frameon=False)
    for bar, value in zip(bars, values):
        axes.text(bar.get_x() + bar.get_width() / 2, value,
                  " {0:.2f}".format(value), ha="center", va="bottom",
                  fontsize=7, color=ARDOISE)
    axes.set_ylabel("Heures", fontsize=8)
    axes.tick_params(labelsize=7)
    axes.set_ylim(0, max(values) * 1.25)
    axes.grid(True, axis="y", linewidth=0.4, color="#d5d8dc")
    axes.set_axisbelow(True)
    for side in ("top", "right"):
        axes.spines[side].set_visible(False)
    figure.tight_layout(pad=0.5)
    figure.savefig(output_path, dpi=DPI, facecolor="white")
    plt.close(figure)
    return output_path if os.path.exists(output_path) else None


def build_all(metrics_values, land_cover, folder):
    """Produit les trois graphiques dans le dossier donne.

    Renvoie un dictionnaire {cle: chemin ou None}.
    """
    os.makedirs(folder, exist_ok=True)
    metrics_values = metrics_values or {}
    corine = (land_cover or {}).get("corine") or {}
    return {
        "hypsometrie": hypsometric_curve(
            metrics_values.get("hypsometrie"),
            os.path.join(folder, "hypsometrie.png"),
        ),
        "occupation": land_cover_pie(
            corine.get("niveaux1"),
            os.path.join(folder, "occupation.png"),
        ),
        "temps": concentration_times(
            metrics_values.get("temps_concentration"),
            os.path.join(folder, "temps_concentration.png"),
        ),
    }
