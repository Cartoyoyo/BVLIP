# -*- coding: utf-8 -*-
"""Genere icons/icon.png (barre d'outils) et icons/logo.png (A propos).

Outil de developpement : a relancer uniquement si l'identite visuelle change.
Le motif est le meme dans les deux tailles : la ligne de partage des eaux du
bassin, son chevelu hydrographique, et l'exutoire en rouge a l'aval.

    python tools/make_icons.py
"""

import os

from PIL import Image, ImageDraw

ICONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons")

BACKGROUND = (44, 62, 80, 255)     # bleu ardoise, la couleur des boutons
BASIN_FILL = (52, 152, 219, 90)    # remplissage translucide du bassin
BASIN_LINE = (236, 240, 241, 255)  # ligne de partage des eaux (sur fond fonce)
BASIN_LINE_ALT = (44, 62, 80, 255)  # la meme, sur fond clair (logo detoure)
STREAM = (93, 173, 226, 255)       # chevelu hydrographique
OUTLET = (231, 76, 60, 255)        # exutoire

# Trace normalise dans un carre [0, 1], mis a l'echelle a la taille voulue.
BASIN = [
    (0.50, 0.90), (0.30, 0.80), (0.16, 0.62), (0.14, 0.40), (0.26, 0.22),
    (0.46, 0.12), (0.68, 0.14), (0.84, 0.28), (0.88, 0.52), (0.78, 0.74),
    (0.62, 0.86),
]
STREAMS = [
    [(0.50, 0.90), (0.50, 0.70), (0.47, 0.52), (0.42, 0.34), (0.38, 0.22)],
    [(0.47, 0.52), (0.60, 0.44), (0.70, 0.32), (0.74, 0.22)],
    [(0.50, 0.70), (0.34, 0.60), (0.24, 0.46)],
    [(0.60, 0.44), (0.66, 0.56), (0.76, 0.62)],
]
OUTLET_POINT = (0.50, 0.90)


def _scale(points, size, margin):
    span = size - 2 * margin
    return [(margin + x * span, margin + y * span) for x, y in points]


def draw_icon(size, with_background=True):
    """Dessine le motif a la taille demandee, en supersampling x4."""
    factor = 4
    big = size * factor
    image = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    margin = big * 0.06
    if with_background:
        radius = int(big * 0.18)
        draw.rounded_rectangle(
            [(0, 0), (big - 1, big - 1)], radius=radius, fill=BACKGROUND
        )
        margin = big * 0.14

    basin = _scale(BASIN, big, margin)
    draw.polygon(basin, fill=BASIN_FILL)
    draw.line(basin + [basin[0]],
              fill=BASIN_LINE if with_background else BASIN_LINE_ALT,
              width=max(2, int(big * 0.028)), joint="curve")

    for branch in STREAMS:
        draw.line(_scale(branch, big, margin), fill=STREAM,
                  width=max(2, int(big * 0.022)), joint="curve")

    ox, oy = _scale([OUTLET_POINT], big, margin)[0]
    r = big * 0.055
    draw.ellipse([(ox - r, oy - r), (ox + r, oy + r)], fill=OUTLET,
                 outline=(255, 255, 255, 255), width=max(1, int(big * 0.012)))

    return image.resize((size, size), Image.LANCZOS)


def main():
    os.makedirs(ICONS_DIR, exist_ok=True)
    draw_icon(96).save(os.path.join(ICONS_DIR, "icon.png"))
    draw_icon(320, with_background=False).save(
        os.path.join(ICONS_DIR, "logo.png")
    )
    print("icon.png (96) et logo.png (320) generes dans", ICONS_DIR)


if __name__ == "__main__":
    main()
