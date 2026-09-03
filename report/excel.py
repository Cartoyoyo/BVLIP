# -*- coding: utf-8 -*-
"""Version tableur du rapport, mise en forme comme la page A4.

Meme organisation que le PDF : le titre, puis l'image du bassin, puis les
caracteristiques et les graphiques. Un second onglet porte le detail que la
page A4 ne peut pas contenir, et un troisieme le releve des cours d'eau amont.

Les valeurs numeriques sont ecrites comme des nombres, pas comme du texte mis
en forme : le tableur reste un outil de calcul, et une surface recopiee dans
une formule doit s'additionner sans retraitement. La presentation passe donc
par les formats de nombre, jamais par des chaines pre-formatees.

openpyxl et Pillow sont livres avec l'installation Windows de QGIS. En leur
absence, la fonction renvoie None et seul le PDF est produit.
"""

import os
from datetime import datetime

# Couleurs, reprises de la mise en page A4.
ARDOISE = "FF2C3E50"
BLEU = "FF2980B9"
GRIS = "FF7F8C8D"
FILET = "FFE5E8EA"
BANDE = "FFF4F6F7"

TITLE_ROW = 1
SUBTITLE_ROW = 2
IMAGE_ROW = 4
ROW_HEIGHT_PX = 20        # hauteur de ligne par defaut d'Excel

COL_LABEL = "A"
COL_VALUE = "B"

# Le classeur s'imprime en A4 portrait comme le PDF. La zone imprimable vaut
# 210 mm moins deux marges de 12 mm, soit 186 mm : a 96 points par pouce,
# environ 700 pixels.
#
# Les deux colonnes doivent couvrir cette largeur a elles seules, car la zone
# d'impression est bornee a A:B. Une image plus large que A+B se retrouve
# coupee net a l'impression alors qu'elle s'affiche entiere a l'ecran : le
# defaut ne se voit qu'a l'apercu avant impression.
#
# Largeur d'une colonne Excel en pixels : sa largeur nominale fois sept, plus
# cinq. A 70 et B 28 donnent donc 495 + 201 = 696 pixels.
A4_CONTENT_PX = 700
COL_LABEL_WIDTH = 70      # environ 131 mm, de quoi loger les intitules longs
COL_VALUE_WIDTH = 28      # environ 53 mm

IMAGE_WIDTH_PX = 660      # la carte, un peu en retrait des marges
CHART_WIDTH_PX = 600

# Les graphiques sont places sous le tableau et non a sa droite comme sur la
# page A4 : cote a cote, la largeur du classeur atteindrait le double d'une
# feuille et rien ne tiendrait plus en portrait.


def available():
    """Le classeur peut-il etre produit dans cette installation ?"""
    try:
        import openpyxl  # noqa: F401
        from openpyxl.drawing.image import Image  # noqa: F401
        return True
    except ImportError:
        return False


_PRECISIONS = None


def _number_format(name, value):
    """Format de nombre, cale sur la precision declaree du champ.

    Chaque champ porte deja sa precision dans core.results.BASIN_FIELDS : une
    part en pourcentage en demande une, un indice de compacite trois, un
    nombre de batiments aucune. La reprendre ici evite d'afficher quinze
    decimales sur une valeur qui n'en signifie qu'une, et garantit que le
    tableur montre exactement ce que montre le PDF.
    """
    from ..core.results import BASIN_FIELDS

    global _PRECISIONS
    if _PRECISIONS is None:
        _PRECISIONS = {entry[0]: entry[3] for entry in BASIN_FIELDS}

    digits = _PRECISIONS.get(name)
    if digits is None:
        digits = 0 if isinstance(value, int) else 2
    return "# ##0" if digits <= 0 else "# ##0." + "0" * digits


def _write_pair(sheet, row, name, label, value, styles):
    cell_label = sheet["{0}{1}".format(COL_LABEL, row)]
    cell_label.value = label
    cell_label.font = styles["label"]
    cell_label.border = styles["rule"]
    cell_label.alignment = styles["left"]

    cell_value = sheet["{0}{1}".format(COL_VALUE, row)]
    cell_value.border = styles["rule"]
    cell_value.alignment = styles["right"]
    cell_value.font = styles["value"]
    if isinstance(value, bool):
        cell_value.value = "oui" if value else "non"
    elif isinstance(value, (int, float)):
        cell_value.value = value
        cell_value.number_format = _number_format(name, value)
    else:
        cell_value.value = str(value)
        cell_value.alignment = styles["left_bold"]


def _write_section(sheet, row, title, styles):
    cell = sheet["{0}{1}".format(COL_LABEL, row)]
    cell.value = title
    cell.font = styles["section"]
    cell.fill = styles["band"]
    sheet["{0}{1}".format(COL_VALUE, row)].fill = styles["band"]
    return row + 1


def _setup_a4(sheet, last_row, last_column=COL_VALUE):
    """Regle l'onglet pour une impression A4 portrait.

    fitToWidth force le contenu a tenir en largeur sur une page ; la hauteur
    reste libre, l'onglet s'imprime donc sur autant de pages que necessaire
    sans jamais couper une colonne au milieu.
    """
    from openpyxl.worksheet.page import PageMargins
    from openpyxl.worksheet.properties import PageSetupProperties

    sheet.page_setup.orientation = "portrait"
    sheet.page_setup.paperSize = sheet.PAPERSIZE_A4
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.fitToHeight = 0
    sheet.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    sheet.page_margins = PageMargins(
        left=0.47, right=0.47, top=0.55, bottom=0.55,
        header=0.3, footer=0.3,
    )
    sheet.print_area = "A1:{0}{1}".format(last_column, last_row)


def _insert_image(sheet, path, anchor, width_px=None, height_px=None):
    """Insere une image redimensionnee et renvoie sa hauteur posee, ou 0.

    La hauteur sert a savoir combien de lignes reserver dessous : Excel ne
    fait pas circuler le contenu autour d'une image, elle flotte au-dessus des
    cellules et masquerait le tableau si on ne laissait pas la place.
    """
    if not path or not os.path.exists(path):
        return 0
    from openpyxl.drawing.image import Image

    image = Image(path)
    if height_px and image.height != height_px:
        ratio = height_px / float(image.height)
        image.height = height_px
        image.width = int(image.width * ratio)
    if width_px and image.width != width_px:
        ratio = width_px / float(image.width)
        image.width = width_px
        image.height = int(image.height * ratio)
    image.anchor = anchor
    sheet.add_image(image)
    return image.height


def build_workbook(values, land_cover, streams_layer, charts_paths, map_image,
                   output_path, title, subtitle):
    """Ecrit le classeur et renvoie son chemin, ou None si openpyxl manque."""
    if not available():
        return None

    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

    from ..core.results import ALIASES, REPORT_SECTIONS

    thin = Side(style="thin", color=FILET)
    styles = {
        "title": Font(name="Calibri", size=18, bold=True, color=ARDOISE),
        "subtitle": Font(name="Calibri", size=10, color=GRIS),
        "section": Font(name="Calibri", size=11, bold=True, color=BLEU),
        "label": Font(name="Calibri", size=10, color=ARDOISE),
        "value": Font(name="Calibri", size=10, bold=True, color=ARDOISE),
        "footer": Font(name="Calibri", size=8, color=GRIS),
        "band": PatternFill("solid", fgColor=BANDE),
        "rule": Border(bottom=thin),
        "left": Alignment(horizontal="left", vertical="center",
                          wrap_text=True),
        "left_bold": Alignment(horizontal="left", vertical="center",
                               wrap_text=True),
        "right": Alignment(horizontal="right", vertical="center"),
    }

    book = Workbook()
    sheet = book.active
    sheet.title = "Bassin versant"
    sheet.sheet_view.showGridLines = False
    sheet.column_dimensions[COL_LABEL].width = COL_LABEL_WIDTH
    sheet.column_dimensions[COL_VALUE].width = COL_VALUE_WIDTH

    sheet["A{0}".format(TITLE_ROW)] = title
    sheet["A{0}".format(TITLE_ROW)].font = styles["title"]
    sheet.row_dimensions[TITLE_ROW].height = 26
    sheet["A{0}".format(SUBTITLE_ROW)] = subtitle
    sheet["A{0}".format(SUBTITLE_ROW)].font = styles["subtitle"]

    # --- La carte, en haut, comme sur la page A4
    rows_used = 2
    height = _insert_image(sheet, map_image, "A{0}".format(IMAGE_ROW),
                           width_px=IMAGE_WIDTH_PX)
    if height:
        rows_used = height // ROW_HEIGHT_PX + 2
    row = IMAGE_ROW + rows_used

    # --- Les caracteristiques, section par section
    for section, names in REPORT_SECTIONS:
        pairs = [(n, ALIASES.get(n, n), values.get(n))
                 for n in names if values.get(n) not in (None, "")]
        if not pairs:
            continue
        row = _write_section(sheet, row, section, styles)
        for name, label, value in pairs:
            _write_pair(sheet, row, name, label, value, styles)
            row += 1
        row += 1

    # --- Les graphiques, sous le tableau
    for key in ("hypsometrie", "occupation", "temps"):
        path = (charts_paths or {}).get(key)
        if not path:
            continue
        height = _insert_image(sheet, path, "A{0}".format(row),
                               width_px=CHART_WIDTH_PX)
        if height:
            row += height // ROW_HEIGHT_PX + 2

    row += 1
    sheet["A{0}".format(row)] = (
        "Produit par BVLIP le {0}. Sources : RGE ALTI et BD TOPO (IGN), "
        "Corine Land Cover 2018, référentiel des masses d'eau Sandre, "
        "fond de plan IGN v2.".format(
            datetime.now().strftime("%d/%m/%Y à %H:%M"))
    )
    sheet["A{0}".format(row)].font = styles["footer"]
    _setup_a4(sheet, row)

    _sheet_land_cover(book, land_cover, styles)
    _sheet_streams(book, streams_layer, styles)

    book.save(output_path)
    return output_path


def _sheet_land_cover(book, land_cover, styles):
    """Detail Corine Land Cover niveau 3, absent de la page A4."""
    corine = (land_cover or {}).get("corine") or {}
    classes = corine.get("classes") or []
    if not classes:
        return
    sheet = book.create_sheet("Occupation du sol")
    sheet.sheet_view.showGridLines = False
    sheet.column_dimensions["A"].width = 10
    sheet.column_dimensions["B"].width = 52
    sheet.column_dimensions["C"].width = 16
    sheet.column_dimensions["D"].width = 16

    for column, label in (("A", "Code CLC"), ("B", "Classe"),
                          ("C", "Surface (ha)"), ("D", "Part (% du bassin)")):
        cell = sheet["{0}1".format(column)]
        cell.value = label
        cell.font = styles["section"]
        cell.fill = styles["band"]

    last_row = 1
    for index, item in enumerate(classes, start=2):
        sheet["A{0}".format(index)] = item["code"]
        sheet["B{0}".format(index)] = item["libelle"]
        sheet["C{0}".format(index)] = item["surface_ha"]
        sheet["C{0}".format(index)].number_format = "0.00"
        sheet["D{0}".format(index)] = item["part_pct"]
        sheet["D{0}".format(index)].number_format = "0.0"
        for column in "ABCD":
            sheet["{0}{1}".format(column, index)].border = styles["rule"]
        last_row = index

    bati = (land_cover or {}).get("bati") or {}
    if bati.get("batiment_nb") is not None:
        row = last_row + 2
        sheet["A{0}".format(row)] = "Bâti mesuré sur la BD TOPO"
        sheet["A{0}".format(row)].font = styles["section"]
        for offset, (label, value, fmt) in enumerate((
            ("Nombre de bâtiments", bati.get("batiment_nb"), "# ##0"),
            ("Emprise au sol (ha)", bati.get("batiment_ha"), "0.000"),
            ("Emprise au sol (% du bassin)", bati.get("batiment_pct"), "0.00"),
            ("Zones d'habitation (% du bassin)",
             bati.get("zone_habitation_pct"), "0.00"),
        ), start=1):
            sheet["B{0}".format(row + offset)] = label
            sheet["C{0}".format(row + offset)] = value
            sheet["C{0}".format(row + offset)].number_format = fmt
            last_row = row + offset
    _setup_a4(sheet, last_row, "D")


def _sheet_streams(book, streams_layer, styles):
    """Releve des cours d'eau amont, avec la longueur de chaque troncon."""
    if streams_layer is None or not streams_layer.featureCount():
        return
    sheet = book.create_sheet("Cours d'eau amont")
    sheet.sheet_view.showGridLines = False
    sheet.column_dimensions["A"].width = 40
    sheet.column_dimensions["B"].width = 26

    for column, label in (("A", "Identifiant BD TOPO du tronçon"),
                          ("B", "Longueur du tronçon (m)")):
        cell = sheet["{0}1".format(column)]
        cell.value = label
        cell.font = styles["section"]
        cell.fill = styles["band"]

    total = 0.0
    row = 2
    for feature in streams_layer.getFeatures():
        sheet["A{0}".format(row)] = feature["cleabs"]
        length = feature["longueur_m"] or 0.0
        sheet["B{0}".format(row)] = length
        sheet["B{0}".format(row)].number_format = "# ##0.0"
        for column in "AB":
            sheet["{0}{1}".format(column, row)].border = styles["rule"]
        total += length
        row += 1

    sheet["A{0}".format(row + 1)] = "Linéaire total (m)"
    sheet["A{0}".format(row + 1)].font = styles["value"]
    sheet["B{0}".format(row + 1)] = total
    sheet["B{0}".format(row + 1)].number_format = "# ##0.0"
    sheet["B{0}".format(row + 1)].font = styles["value"]
    _setup_a4(sheet, row + 1)
