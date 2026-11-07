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
    return "#,##0" if digits <= 0 else "#,##0." + "0" * digits


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


def _title_row(sheet, row, text, styles):
    """Titre de bloc, dans un onglet qui en reunit plusieurs."""
    sheet.cell(row=row, column=1, value=text).font = styles["section"]
    return row + 1


def _header_row(sheet, row, labels, styles):
    """En-tetes de colonnes, a partir de la colonne A ; None saute une case."""
    for index, label in enumerate(labels, start=1):
        if label is None:
            continue
        cell = sheet.cell(row=row, column=index, value=label)
        cell.font = styles["section"]
        cell.fill = styles["band"]
        cell.alignment = styles["left"]
    return row + 1


def _data_row(sheet, row, cells, styles, formats=None):
    """Une ligne de tableau. formats : {numero de colonne: format}."""
    for index, value in enumerate(cells, start=1):
        cell = sheet.cell(row=row, column=index, value=value)
        cell.border = styles["rule"]
        fmt = (formats or {}).get(index)
        if fmt and isinstance(value, (int, float)) \
                and not isinstance(value, bool):
            cell.number_format = fmt
    return row + 1


def _pair_row(sheet, row, label, value, fmt=None):
    """Un intitule en B et sa valeur en C, comme dans l'onglet agricole."""
    sheet.cell(row=row, column=2, value=label)
    cell = sheet.cell(row=row, column=3, value=value)
    if fmt and isinstance(value, (int, float)) and not isinstance(value, bool):
        cell.number_format = fmt
    return row + 1


def _note_row(sheet, row, text, styles, height=None):
    cell = sheet.cell(row=row, column=1, value=text)
    cell.font = styles["footer"]
    cell.alignment = styles["left"]
    if height:
        sheet.row_dimensions[row].height = height
    return row + 1


def _theme_sheet(book, title, widths):
    """Onglet d'un theme, colonnes dimensionnees pour tous ses blocs."""
    sheet = book.create_sheet(title)
    sheet.sheet_view.showGridLines = False
    for column, width in zip("ABCDEFGHIJKL", widths):
        sheet.column_dimensions[column].width = width
    return sheet


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
                   output_path, title, subtitle, protected=None,
                   structures=None, steu=None, population=None,
                   prelevements=None, agriculture=None, result=None):
    """Ecrit le classeur et renvoie son chemin, ou None si openpyxl manque.

    Une synthese en tuiles ouvre le classeur. Viennent ensuite la fiche du
    bassin, un onglet par theme dans l'ordre des sections du PDF -
    occupation du sol, agriculture, nature et biodiversite, eau, obstacles,
    pression anthropique -, les indicateurs a plat, les sources et le releve
    des cours d'eau. result porte le resultat complet du traitement, pour les
    donnees que les autres arguments ne transmettent pas.
    """
    result = result or {}
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
    for key in ("hypsometrie", "occupation", "zonages"):
        path = (charts_paths or {}).get(key)
        if not path:
            continue
        height = _insert_image(sheet, path, "A{0}".format(row),
                               width_px=CHART_WIDTH_PX)
        if height:
            row += height // ROW_HEIGHT_PX + 2

    row += 1
    sheet["A{0}".format(row)] = (
        "Produit par BVLIP le {0}. Sources : RGE ALTI, BD TOPO et BD Forêt "
        "v2 (IGN), Corine Land Cover 2018, zonages INPN / Patrinat, "
        "référentiels Sandre (masses d'eau, hydroécorégions, ROE, STEU, "
        "SAGE), Hub'Eau, Vigicrues, Géorisques, GBIF, fond de plan IGN v2.".format(
            datetime.now().strftime("%d/%m/%Y à %H:%M"))
    )
    sheet["A{0}".format(row)].font = styles["footer"]
    row += 1
    from .layout import AVERTISSEMENT
    sheet["A{0}".format(row)] = AVERTISSEMENT
    sheet["A{0}".format(row)].font = Font(name="Calibri", size=8, bold=True,
                                          color="FFB03A2E")
    _setup_a4(sheet, row)

    _sheet_land_cover(book, land_cover, styles)
    _sheet_agriculture(book, agriculture, styles)
    _sheet_protected(book, protected, styles, result.get("biodiversite"))
    _sheet_water(book, result, structures, prelevements, styles)
    _sheet_obstacles(book, structures, styles)
    _sheet_pressions(book, steu, population, values, prelevements,
                     result.get("pressions"), styles)
    _sheet_indicateurs(book, values, styles)
    _sheet_sources(book, styles)
    _sheet_streams(book, streams_layer, styles)
    # La synthese est ecrite en dernier, parce que ses liens visent des
    # onglets qui doivent deja exister, puis remise en tete du classeur.
    _sheet_synthese(book, values, title, subtitle, styles)

    # L'avertissement du PDF, en pied d'impression de chaque onglet.
    from .layout import AVERTISSEMENT
    for each in book.worksheets:
        each.oddFooter.center.text = AVERTISSEMENT
        each.oddFooter.center.size = 7
        each.oddFooter.center.color = "B03A2E"

    book.save(output_path)
    return output_path


# ------------------------------------------------------------- Synthese
#
# Une tuile par indicateur majeur, rangees par theme, chacune renvoyant a
# l'onglet de son detail. C'est l'onglet qu'un elu ou un partenaire lit sans
# aller plus loin : il doit tenir sur un ecran et se comparer d'un bassin a
# l'autre, d'ou des indicateurs toujours les memes, dans le meme ordre.
#
# (theme, couleur, onglet de detail, tuiles). Une tuile :
# (champ, intitule, format de nombre, sous-titre, barre de part du bassin,
#  onglet de detail s'il differe de celui du theme). Le sous-titre est une
# chaine a trous remplie avec les valeurs du bassin, ou None ; une tuile dont
# le champ est vide - donnee non demandee - n'est pas posee.
SYNTHESE = (
    ("Occupation du sol", "8D6E63", "Occupation du sol", (
        ("ocs_dom_pct", "Occupation dominante (Corine)", '0" %"',
         "{ocs_dominante}", True, None),
        ("peupl_pct", "Surface boisée (BD Forêt)", '0.0" %"',
         None, True, None),
        ("chab_hum_pct", "Sols humides (CarHab)", '0.0" %"',
         "couverture CarHab {chab_cov_pct:.0f} %", True, None),
        ("bati_pct", "Emprise du bâti", '0.00" %"',
         "{bati_nb} bâtiments", False, None),
    )),
    ("Agriculture", "5D8C3A", "Agriculture", (
        ("rpg_pct", "Surface déclarée à la PAC", '0.0" %"',
         "dont herbe {herbe_pct:.1f} % du bassin", True, None),
        ("haies_dens", "Densité de haies", '0.0" m/ha"',
         "{haies_km:.0f} km de haies", False, None),
        ("onf_pct", "Forêts publiques (ONF)", '0.0" %"',
         "{onf_ha:.0f} ha", True, None),
        ("bio_pct", "Agriculture biologique certifiée", '0.0" %"',
         None, True, None),
    )),
    ("Nature et biodiversité", "2E9E5B", "Nature et biodiversité", (
        ("zonage_pct", "Sous zonage environnemental", '0.0" %"',
         "{zonage_nb} sites, sans double compte", True, None),
        ("gbif_esp_nb", "Espèces observées (GBIF)", "#,##0",
         "{gbif_obs_nb} observations publiées", False, None),
    )),
    ("Eau", "1F6FA3", "Eau", (
        ("me_code_eu", "Masse d'eau DCE", None, "{me_nom}", False, None),
        ("aep_nb", "Ouvrages pour l'eau potable", "0",
         "{aep_vol_m3:.0f} m³ prélevés par an", False, None),
        ("roe_nb", "Obstacles à l'écoulement", "0",
         "{roe_par_km:.2f} par km de cours d'eau", False,
         "Obstacles (ROE)"),
        ("vigi_km", "Cours d'eau surveillés (Vigicrues)", '0.0" km"',
         "{vigi_st_nb} station(s) de mesure", False, None),
    )),
    ("Pression anthropique", "B5452F", "Pression anthropique", (
        ("population_est", "Population estimée", '#,##0" hab."',
         "{densite_hab_km2:.1f} hab./km² · estimation", False, None),
        ("steu_nb", "Stations d'épuration", "0",
         "{steu_capa_tot_eh:.0f} EH de capacité", False, None),
        ("preleve_vol_m3", "Prélèvements d'eau", '#,##0" m³/an"',
         "{preleve_nb} ouvrage(s)", False, None),
        ("basias_nb", "Anciens sites industriels (BASIAS)", "0",
         "BASOL {basol_nb} · SIS {sis_nb}", False, None),
        ("irep_nb", "Établissements déclarant leurs rejets", "0",
         None, False, None),
    )),
)

# Colonnes des tuiles : quatre tuiles de deux colonnes, separees par une
# colonne etroite. B-C, E-F, H-I, K-L.
TILE_COLUMNS = (2, 5, 8, 11)
TILE_WIDTH = 14
TILE_GAP = 2

# Sous-titre d'une tuile, au-dela duquel il est coupe : ce que deux colonnes
# de quatorze logent en corps 8,5.
TILE_SUB_MAX = 42


def _tint(color, ratio=0.65):
    """Teinte claire d'une couleur, melangee de blanc : fond des barres."""
    red, green, blue = (int(color[i:i + 2], 16) for i in (0, 2, 4))
    mix = [int(c + (255 - c) * ratio) for c in (red, green, blue)]
    return "FF{0:02X}{1:02X}{2:02X}".format(*mix)


def _fill_holes(template, values):
    """Sous-titre d'une tuile, ou None s'il lui manque une valeur.

    Les nombres sont rendus a la francaise, espace en separateur de milliers
    et virgule decimale : c'est du texte, pas une cellule de calcul.
    """
    if not template:
        return None
    try:
        text = template.format(**{
            key: value for key, value in values.items()
            if value not in (None, "")
        })
    except (KeyError, ValueError, TypeError):
        return None
    return text


def _french_numbers(text):
    """1234.5 -> 1 234,5 dans un texte deja forme."""
    import re

    def repl(match):
        number = match.group(0)
        whole, _, decimals = number.partition(".")
        whole = "{:,}".format(int(whole)).replace(",", " ")
        return whole + ("," + decimals if decimals else "")
    return re.sub(r"\d+(?:\.\d+)?", repl, text)


def _tile(sheet, top, left, color, label, value, fmt, sub, link, bar):
    """Une tuile de quatre lignes sur deux colonnes, filet de couleur en haut."""
    from openpyxl.formatting.rule import DataBarRule
    from openpyxl.styles import Alignment, Border, Font, Side
    from openpyxl.utils import get_column_letter

    light = Side(style="thin", color=FILET)
    strong = Side(style="thick", color="FF" + color)
    for offset in range(4):
        sheet.merge_cells(start_row=top + offset, start_column=left,
                          end_row=top + offset, end_column=left + 1)
        for column in (left, left + 1):
            sheet.cell(top + offset, column).border = Border(
                top=strong if offset == 0 else None,
                bottom=light if offset == 3 else None,
                left=light if column == left else None,
                right=light if column == left + 1 else None,
            )

    cell = sheet.cell(top, left, label)
    cell.font = Font(name="Calibri", size=9, color=GRIS)
    cell.alignment = Alignment(vertical="top", wrap_text=True)

    cell = sheet.cell(top + 1, left, value)
    cell.font = Font(name="Calibri", size=16, bold=True, color=ARDOISE)
    cell.alignment = Alignment(horizontal="left", vertical="center",
                               shrink_to_fit=True)
    if fmt and isinstance(value, (int, float)) and not isinstance(value, bool):
        cell.number_format = fmt
    if bar and isinstance(value, (int, float)):
        # La barre dit la part du bassin, de 0 a 100 % : elle se lit avant le
        # chiffre, et deux bassins se comparent d'un coup d'oeil.
        reference = "{0}{1}".format(get_column_letter(left), top + 1)
        sheet.conditional_formatting.add(reference, DataBarRule(
            start_type="num", start_value=0, end_type="num", end_value=100,
            color=_tint(color), showValue=True))

    if sub:
        # Coupe plutot que reduction : une denomination de masse d'eau de
        # quatre-vingts caracteres, reduite pour tenir, devenait illisible.
        sub = _french_numbers(sub)
        if len(sub) > TILE_SUB_MAX:
            sub = sub[:TILE_SUB_MAX - 1].rstrip() + "…"
        cell = sheet.cell(top + 2, left, sub)
        cell.font = Font(name="Calibri", size=8.5, color=GRIS)
        cell.alignment = Alignment(vertical="top")

    if link:
        cell = sheet.cell(top + 3, left, "→ {0}".format(link))
        cell.hyperlink = "#'{0}'!A1".format(link)
        cell.font = Font(name="Calibri", size=8.5, color=BLEU, underline="single")

    sheet.row_dimensions[top].height = 26
    sheet.row_dimensions[top + 1].height = 26
    sheet.row_dimensions[top + 2].height = 15
    sheet.row_dimensions[top + 3].height = 15


def _sheet_synthese(book, values, title, subtitle, styles):
    """Onglet de tete : les indicateurs majeurs en tuiles, par theme."""
    from openpyxl.styles import Font
    from openpyxl.utils import get_column_letter

    sheet = book.create_sheet("Synthèse", 0)
    sheet.sheet_view.showGridLines = False
    sheet.column_dimensions["A"].width = TILE_GAP
    for left in TILE_COLUMNS:
        sheet.column_dimensions[get_column_letter(left)].width = TILE_WIDTH
        sheet.column_dimensions[get_column_letter(left + 1)].width = TILE_WIDTH
        sheet.column_dimensions[get_column_letter(left + 2)].width = TILE_GAP

    sheet["B1"] = title
    sheet["B1"].font = styles["title"]
    sheet.row_dimensions[1].height = 26
    sheet["B2"] = subtitle
    sheet["B2"].font = styles["subtitle"]

    # Grandeurs derivees, que les sous-titres citent sans qu'elles soient
    # des champs du bassin.
    values = dict(values)
    if values.get("population_est") is not None and values.get("surface_km2"):
        values["densite_hab_km2"] = (values["population_est"]
                                     / values["surface_km2"])

    row = 4
    for theme, color, detail, tiles in SYNTHESE:
        posees = [tile for tile in tiles
                  if values.get(tile[0]) not in (None, "")]
        if not posees:
            continue
        cell = sheet.cell(row, 2, theme)
        cell.font = Font(name="Calibri", size=11, bold=True, color="FF" + color)
        row += 1
        # Quatre tuiles par rangee ; un theme qui en a davantage passe a la
        # ligne plutot que de deborder de la page.
        for start in range(0, len(posees), len(TILE_COLUMNS)):
            rangee = posees[start:start + len(TILE_COLUMNS)]
            for index, (field, label, fmt, sub, bar, target) in enumerate(
                    rangee):
                target = target or detail
                _tile(sheet, row, TILE_COLUMNS[index], color, label,
                      values.get(field), fmt, _fill_holes(sub, values),
                      target if target in book.sheetnames else None, bar)
            row += 5

    sheet.cell(row, 2, "Carte et fiche complète dans l'onglet Bassin versant, "
                       "détail de chaque thème dans les onglets suivants, "
                       "indicateurs à plat dans l'onglet Indicateurs."
               ).font = styles["footer"]

    # Une page paysage, tuiles seules. La carte n'y est pas reprise : elle
    # ouvre deja l'onglet du bassin, et une image flottante ignore les sauts
    # de page d'une impression ajustee - elle chevauchait les deux pages.
    _setup_a4(sheet, row, "L")
    sheet.page_setup.orientation = "landscape"
    sheet.page_setup.fitToHeight = 1
    book.active = 0


# ---------------------------------------------------------- Indicateurs
#
# Les memes valeurs que la table du bassin, une par ligne : c'est la forme
# que demandent un tableau croise, une jointure SIG ou la comparaison de
# plusieurs bassins - on colle les onglets de dix classeurs les uns sous les
# autres et l'on filtre. Aucune fusion, aucune decoration.

# Theme de chaque groupe de champs, dans le vocabulaire des onglets.
THEME_OF_GROUP = {
    "identite": "Identité et exutoire",
    "metriques": "Forme, relief et hydrographie",
    "ocs": "Occupation du sol", "foret": "Occupation du sol",
    "carhab": "Occupation du sol",
    "agri": "Agriculture", "haies": "Agriculture", "onf": "Agriculture",
    "zonages": "Nature et biodiversité", "gbif": "Nature et biodiversité",
    "masse_eau": "Eau", "meso": "Eau", "her": "Eau", "sage": "Eau",
    "vigicrues": "Eau",
    "roe": "Obstacles et stations", "hydrometrie": "Obstacles et stations",
    "steu": "Pression anthropique", "prelevements": "Pression anthropique",
    "population": "Pression anthropique", "pressions": "Pression anthropique",
}

# Champs rattaches a un autre theme que celui de leur groupe : l'eau potable
# se lit avec l'eau, meme si elle sort du releve des prelevements.
THEME_OF_FIELD = {"aep_nb": "Eau", "aep_vol_m3": "Eau"}


def _split_unit(label):
    """(intitule sans unite, unite) d'apres l'intitule complet du champ."""
    import re

    found = re.match(r"^(.*?)\s*\(([^()]*)\)\s*$", label)
    if found:
        unit = found.group(2)
        return found.group(1), "" if unit == "sans unité" else unit
    if label.endswith(" — nombre"):
        return label[:-len(" — nombre")], "nombre"
    return label, ""


def _sheet_indicateurs(book, values, styles):
    """Indicateurs du bassin au format long, un par ligne."""
    from openpyxl.styles import Font

    from ..core.results import BASIN_FIELDS

    sheet = _theme_sheet(book, "Indicateurs", (24, 28, 16, 58, 16, 22))
    headers = ("id_bv", "Thème", "Champ", "Indicateur", "Valeur", "Unité")
    for index, label in enumerate(headers, start=1):
        sheet.cell(1, index, label).font = Font(name="Calibri", size=10,
                                                bold=True)
    row = 2
    for name, _kind, _length, _precision, key, label in BASIN_FIELDS:
        value = values.get(name)
        if value in (None, "") or name == "id_bv":
            continue
        group = key.partition(".")[0]
        text, unit = _split_unit(label)
        if isinstance(value, bool):
            value = "oui" if value else "non"
        sheet.cell(row, 1, values.get("id_bv"))
        sheet.cell(row, 2, THEME_OF_FIELD.get(
            name, THEME_OF_GROUP.get(group, group)))
        sheet.cell(row, 3, name)
        sheet.cell(row, 4, text)
        cell = sheet.cell(row, 5, value)
        if isinstance(value, (int, float)):
            cell.number_format = _number_format(name, value)
        sheet.cell(row, 6, unit)
        row += 1
    sheet.auto_filter.ref = "A1:F{0}".format(max(row - 1, 1))
    sheet.freeze_panes = "A2"
    _setup_a4(sheet, row - 1, "F")


def _sheet_land_cover(book, land_cover, styles):
    """Detail Corine Land Cover niveau 3, absent de la page A4, puis le bati,
    la BD Foret et les habitats CarHab."""
    corine = (land_cover or {}).get("corine") or {}
    classes = corine.get("classes") or []
    carhab = (land_cover or {}).get("carhab") or {}
    if not classes and not carhab.get("nb"):
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
            ("Nombre de bâtiments", bati.get("batiment_nb"), "#,##0"),
            ("Emprise au sol (ha)", bati.get("batiment_ha"), "0.000"),
            ("Emprise au sol (% du bassin)", bati.get("batiment_pct"), "0.00"),
            ("Zones d'habitation (% du bassin)",
             bati.get("zone_habitation_pct"), "0.00"),
        ), start=1):
            sheet["B{0}".format(row + offset)] = label
            sheet["C{0}".format(row + offset)] = value
            sheet["C{0}".format(row + offset)].number_format = fmt
            last_row = row + offset

    # La BD Foret prolonge la meme feuille plutot que d'en ouvrir une : c'est
    # de l'occupation du sol, mesuree a une autre echelle. Les surfaces ne
    # s'additionnent pas a celles de CLC, et les tenir cote a cote le rappelle.
    forest = (land_cover or {}).get("foret") or {}
    formations = forest.get("formations") or []
    if formations:
        row = last_row + 2
        sheet["A{0}".format(row)] = "Couvert forestier (BD Forêt v2)"
        sheet["A{0}".format(row)].font = styles["section"]
        row += 1
        for column, label in (("B", "Formation végétale"),
                              ("C", "Surface (ha)"),
                              ("D", "Part (% du bassin)")):
            cell = sheet["{0}{1}".format(column, row)]
            cell.value = label
            cell.font = styles["section"]
            cell.fill = styles["band"]
        row += 1
        for item in formations:
            sheet["B{0}".format(row)] = item["libelle"]
            sheet["C{0}".format(row)] = item["surface_ha"]
            sheet["C{0}".format(row)].number_format = "0.00"
            sheet["D{0}".format(row)] = item["part_pct"]
            sheet["D{0}".format(row)].number_format = "0.0"
            for column in "BCD":
                sheet["{0}{1}".format(column, row)].border = styles["rule"]
            row += 1
        last_row = row

    if carhab.get("nb"):
        row = last_row + 2
        row = _title_row(sheet, row, "Habitats CarHab", styles)
        row = _pair_row(sheet, row, "Couverture du bassin par CarHab (%)",
                        carhab.get("couverture_pct"), "0.0")
        row = _pair_row(sheet, row, "Sols humides à aquatiques (ha)",
                        carhab.get("humide_ha"), "0.00")
        row = _pair_row(sheet, row, "Sols humides à aquatiques (% du bassin)",
                        carhab.get("humide_pct"), "0.0")
        for heading, items in (("Humidité du sol", carhab.get("humidites")),
                               ("Physionomie de la végétation",
                                carhab.get("physionomies"))):
            row += 1
            row = _header_row(sheet, row, (None, heading, "Surface (ha)",
                                           "Part (% du bassin)"), styles)
            for item in items or ():
                row = _data_row(sheet, row, (None, item["libelle"],
                                             item["surface_ha"],
                                             item["part_pct"]),
                                styles, {3: "0.00", 4: "0.0"})
        row = _note_row(sheet, row + 1,
                        "CarHab : couverture nationale encore incomplète ; "
                        "les sols humides sont une enveloppe de zones "
                        "humides potentielles, non un inventaire.", styles)
        last_row = row

    _setup_a4(sheet, last_row, "D")


def _sheet_agriculture(book, agriculture, styles):
    """Agriculture declaree a la PAC, comme la section du rapport PDF."""
    agriculture = agriculture or {}
    rpg = agriculture.get("rpg") or {}
    bio = agriculture.get("bio") or {}
    prairies = agriculture.get("prairies") or {}
    aoc = agriculture.get("aoc") or {}
    haies = agriculture.get("haies") or {}
    onf = agriculture.get("onf") or {}
    if not (rpg.get("nb_parcelles") or bio.get("nb_parcelles")
            or prairies.get("nb") or aoc.get("nb") or haies.get("nb")
            or onf.get("nb")):
        return
    sheet = book.create_sheet("Agriculture")
    sheet.sheet_view.showGridLines = False
    sheet.column_dimensions["A"].width = 10
    sheet.column_dimensions["B"].width = 52
    sheet.column_dimensions["C"].width = 16
    sheet.column_dimensions["D"].width = 16

    def header(row, columns):
        for column, label in columns:
            cell = sheet["{0}{1}".format(column, row)]
            cell.value = label
            cell.font = styles["section"]
            cell.fill = styles["band"]
        return row + 1

    def line(row, code, label, surface, part):
        if code is not None:
            sheet["A{0}".format(row)] = code
        sheet["B{0}".format(row)] = label
        sheet["C{0}".format(row)] = surface
        sheet["C{0}".format(row)].number_format = "0.00"
        sheet["D{0}".format(row)] = part
        sheet["D{0}".format(row)].number_format = "0.0"
        for column in "ABCD":
            sheet["{0}{1}".format(column, row)].border = styles["rule"]
        return row + 1

    def title(row, text):
        sheet["A{0}".format(row)] = text
        sheet["A{0}".format(row)].font = styles["section"]
        return row + 1

    surface_columns = (("B", ""), ("C", "Surface (ha)"),
                       ("D", "Part (% du bassin)"))
    row = 1
    if rpg.get("nb_parcelles"):
        row = title(row, "Surface déclarée au RPG")
        for label, value, fmt in (
            ("Surface déclarée (ha)", rpg.get("surface_ha"), "0.00"),
            ("Surface déclarée (% du bassin)", rpg.get("part_pct"), "0.0"),
            ("Parcelles déclarées", rpg.get("nb_parcelles"), "#,##0"),
            ("Taille moyenne (ha)", rpg.get("taille_moyenne_ha"), "0.00"),
            ("Taille médiane (ha)", rpg.get("taille_mediane_ha"), "0.00"),
        ):
            sheet["B{0}".format(row)] = label
            sheet["C{0}".format(row)] = value
            sheet["C{0}".format(row)].number_format = fmt
            row += 1

        if rpg.get("herbe_ha") is not None:
            row += 1
            row = header(row, (("B", "Prairies et cultures"),)
                         + surface_columns[1:])
            row = line(row, None, "Prairies et surfaces pastorales",
                       rpg["herbe_ha"], rpg["herbe_pct"])
            row = line(row, None, "Cultures", rpg["cultures_ha"],
                       rpg["cultures_pct"])

        if rpg.get("categories"):
            row += 1
            row = header(row, (("B", "Catégorie de culture"),)
                         + surface_columns[1:])
            for item in rpg["categories"]:
                row = line(row, None, item["libelle"], item["surface_ha"],
                           item["part_pct"])

        if rpg.get("cultures"):
            row += 1
            row = header(row, (("A", "Code"), ("B", "Culture déclarée"))
                         + surface_columns[1:])
            for item in rpg["cultures"]:
                row = line(row, item["code"], item["libelle"],
                           item["surface_ha"], item["part_pct"])

    others = []
    if bio.get("nb_parcelles"):
        others.append(("Certifiée agriculture biologique",
                       bio.get("certifie_ha"), bio.get("certifie_pct")))
        if bio.get("conversion_ha"):
            others.append(("En conversion vers le biologique",
                           bio.get("conversion_ha"),
                           bio.get("conversion_pct")))
    if prairies.get("nb"):
        others.append(("Prairies sensibles (BCAE, en zone Natura 2000)",
                       prairies.get("surface_ha"), prairies.get("part_pct")))
    if aoc.get("nb"):
        others.append(("Aires AOC viticoles (INAO)", aoc.get("surface_ha"),
                       aoc.get("part_pct")))
    if others:
        row += 1
        row = header(row, (("B", "Engagements et zonages agricoles"),)
                     + surface_columns[1:])
        for label, surface, part in others:
            row = line(row, None, label, surface, part)

    if haies.get("nb"):
        row += 1
        row = title(row, "Haies (dispositif de suivi des bocages)")
        row = _pair_row(sheet, row, "Linéaire de haies (km)",
                        haies.get("longueur_km"), "0.0")
        row = _pair_row(sheet, row, "Densité de haies (m par ha de bassin)",
                        haies.get("densite_m_ha"), "0.0")
        row = _pair_row(sheet, row, "Tronçons de haie", haies.get("nb"),
                        "#,##0")

    if onf.get("nb"):
        row += 1
        row = title(row, "Forêts publiques (ONF)")
        row = header(row, (("A", "Code"), ("B", "Forêt publique"))
                     + surface_columns[1:])
        for foret in onf.get("forets") or ():
            row = line(row, foret["code"],
                       "{0} ({1})".format(foret["nom"], foret["statut"]),
                       foret["surface_ha"], foret["part_pct"])

    row += 1
    sheet["A{0}".format(row)] = (
        "Le RPG ne recense que le déclaré : la surface minore la surface "
        "agricole réelle. Les cultures détaillées sont limitées aux plus "
        "étendues.")
    sheet["A{0}".format(row)].font = styles["footer"]
    _setup_a4(sheet, row, "D")


def _sheet_protected(book, protected, styles, gbif=None):
    """Detail site par site des zonages environnementaux, puis la
    biodiversite observee.

    La page A4 n'en montre que la part du bassin, zonage par zonage. C'est ici
    qu'on trouve les noms : un rapport qui annonce 34 % de ZNIEFF de type I
    sans dire lesquelles n'est pas verifiable, et le lien vers la fiche en
    ligne - INPN, ou europeenne pour Natura 2000 - evite d'avoir a les
    rechercher a la main.
    """
    zonages = (protected or {}).get("zonages") or []
    lignes = [(z, site) for z in zonages for site in z.get("sites") or []]
    if not lignes and not gbif:
        return
    sheet = book.create_sheet("Nature et biodiversité")
    sheet.sheet_view.showGridLines = False
    for column, width in (("A", 30), ("B", 44), ("C", 16), ("D", 14),
                          ("E", 14), ("F", 40)):
        sheet.column_dimensions[column].width = width

    row = 0
    if lignes:
        for column, label in (("A", "Zonage"), ("B", "Site"),
                              ("C", "Code INPN / Sandre"),
                              ("D", "Surface dans le bassin (ha)"),
                              ("E", "Part (% du bassin)"), ("F", "Fiche")):
            cell = sheet["{0}1".format(column)]
            cell.value = label
            cell.font = styles["section"]
            cell.fill = styles["band"]

        row = 2
        for zonage, site in lignes:
            sheet["A{0}".format(row)] = zonage["libelle"]
            sheet["B{0}".format(row)] = site["nom"]
            sheet["C{0}".format(row)] = site["code"]
            sheet["D{0}".format(row)] = site["surface_ha"]
            sheet["D{0}".format(row)].number_format = "0.00"
            sheet["E{0}".format(row)] = site["part_pct"]
            sheet["E{0}".format(row)].number_format = "0.0"
            sheet["F{0}".format(row)] = site["url"]
            for column in "ABCDEF":
                sheet["{0}{1}".format(column, row)].border = styles["rule"]
            row += 1

        # Le total est rappele ici parce que c'est le seul chiffre de la feuille
        # qui ne s'obtienne pas en additionnant la colonne au-dessus : les
        # zonages se recouvrent, et la somme des lignes depasse couramment la
        # surface du bassin.
        row += 1
        sheet["A{0}".format(row)] = "Total sous zonage, sans double compte"
        sheet["A{0}".format(row)].font = styles["value"]
        sheet["D{0}".format(row)] = (protected or {}).get("total_ha")
        sheet["D{0}".format(row)].number_format = "0.00"
        sheet["D{0}".format(row)].font = styles["value"]
        sheet["E{0}".format(row)] = (protected or {}).get("total_pct")
        sheet["E{0}".format(row)].number_format = "0.0"
        sheet["E{0}".format(row)].font = styles["value"]

        # Les liens de l'INPN restent ceux du service, alors que son site
        # ne sert plus les fiches de zones depuis l'incident informatique
        # du Museum. La mention evite de croire le lien faux, et reste
        # vraie une fois le site retabli. Voir protected pour Natura 2000.
        urls = [site["url"] or "" for _, site in lignes]
        notes = []
        if any("inpn.mnhn.fr" in url for url in urls):
            notes.append(
                "Si une fiche INPN ne s'ouvre pas : le site de l'INPN a été "
                "mis en partie hors ligne après un incident informatique au "
                "Muséum (MNHN).")
        if any("biodiversity.europa.eu" in url for url in urls):
            notes.append(
                "Les sites Natura 2000 renvoient vers leur fiche européenne "
                "(BISE, Agence européenne pour l'environnement).")
        if notes:
            row += 1
            for text in notes:
                row += 1
                _note_row(sheet, row, text, styles)

    if gbif:
        row += 2
        row = _title_row(sheet, row, "Biodiversité observée (GBIF)", styles)
        row = _header_row(sheet, row, ("Groupe", None, None,
                                       "Observations", "Espèces"), styles)
        row = _data_row(sheet, row, ("Tous groupes", None, None,
                                     gbif.get("observations"),
                                     gbif.get("especes")),
                        styles, {4: "#,##0", 5: "#,##0"})
        for groupe in gbif.get("groupes") or ():
            row = _data_row(sheet, row, (groupe["libelle"], None, None,
                                         groupe["observations"],
                                         groupe["especes"]),
                            styles, {4: "#,##0", 5: "#,##0"})
        row = _note_row(sheet, row + 1,
                        "Comptes d'observations publiées : ils mesurent "
                        "l'effort d'observation autant que la richesse.",
                        styles)
    _setup_a4(sheet, row, "F")


def _sheet_obstacles(book, structures, styles):
    """Releve des obstacles a l'ecoulement (ROE)."""
    roe = (structures or {}).get("roe") or {}
    if not roe.get("sites"):
        return
    sheet = book.create_sheet("Obstacles (ROE)")
    sheet.sheet_view.showGridLines = False
    for column, width in (("A", 14), ("B", 40), ("C", 18), ("D", 18),
                          ("E", 12), ("F", 12), ("G", 16), ("H", 26)):
        sheet.column_dimensions[column].width = width

    row = 1
    if roe.get("sites"):
        # La provenance de la hauteur a sa colonne : une chute mesuree et un
        # milieu de classe ne se lisent pas de la meme facon, et la moyenne
        # des deux n'aurait pas de sens sans le dire.
        for column, label in (("A", "Code ROE"), ("B", "Nom de l'ouvrage"),
                              ("C", "Type"), ("D", "État"),
                              ("E", "Chute (m)"), ("F", "Provenance"),
                              ("G", "Passe à poissons"),
                              ("H", "Cours d'eau")):
            cell = sheet["{0}{1}".format(column, row)]
            cell.value = label
            cell.font = styles["section"]
            cell.fill = styles["band"]
        row += 1
        for site in roe["sites"]:
            sheet["A{0}".format(row)] = site["code"]
            sheet["B{0}".format(row)] = site["nom"]
            sheet["C{0}".format(row)] = site["type"]
            sheet["D{0}".format(row)] = site["etat"]
            sheet["E{0}".format(row)] = site["chute_m"]
            sheet["E{0}".format(row)].number_format = "0.00"
            sheet["F{0}".format(row)] = site["chute_origine"]
            passe = site["passe_a_poissons"]
            sheet["G{0}".format(row)] = (
                "non renseigné" if passe is None else
                ("oui" if passe else "non")
            )
            sheet["H{0}".format(row)] = site["cours_d_eau"]
            for column in "ABCDEFGH":
                sheet["{0}{1}".format(column, row)].border = styles["rule"]
            row += 1
        row += 1

    _setup_a4(sheet, row, "H")


def _block_population(sheet, row, population, styles, steu=None,
                      values=None):
    """Population estimee du bassin, avec ou sans station d'epuration.

    Elle vivait dans le bloc des STEU et disparaissait avec lui sur un bassin
    sans station. Ce n'est qu'une estimation : voir la methode dans l'onglet
    Sources.
    """
    estimee = (population or {}).get("population_estimee")
    if estimee is None:
        return row
    row = _title_row(sheet, row, "Population estimée", styles)
    row = _pair_row(sheet, row, "Population estimée (habitants)", estimee,
                    "#,##0")
    row = _pair_row(sheet, row, "Communes recoupant le bassin",
                    (population or {}).get("nb_communes"), "0")
    surface_km2 = (values or {}).get("surface_km2")
    if surface_km2:
        row = _pair_row(sheet, row, "Densité estimée (hab./km²)",
                        estimee / surface_km2, "0.0")
    lin_hydro_km = (values or {}).get("lin_hydro_km")
    if lin_hydro_km:
        row = _pair_row(sheet, row,
                        "Population estimée par km de cours d'eau (hab./km)",
                        estimee / lin_hydro_km, "0.0")
    if (steu or {}).get("capacite_totale_eh") and estimee:
        row = _pair_row(sheet, row,
                        "Capacité STEU cumulée pour cette population "
                        "(EH/habitant)",
                        steu["capacite_totale_eh"] / estimee, "0.00")
    return row + 1


def _block_steu(sheet, row, steu, styles):
    """Releve des STEU, a partir de la ligne donnee."""
    stations = (steu or {}).get("stations") or []
    if not stations:
        return row
    row = _title_row(sheet, row, "Stations de traitement des eaux usées "
                                 "(STEU)", styles)

    for column, label in (
        ("A", "Code Sandre"), ("B", "Nom de la station"),
        ("C", "Capacité (EH)"), ("D", "Charge max. entrante (EH)"),
        ("E", "Taux de charge (%)"), ("F", "Nature du traitement"),
        ("G", "En service"), ("H", "Zone sensible"),
        ("I", "Nom de la zone sensible"), ("J", "Autosurveillance"),
        ("K", "Conformité autosurveillance"), ("L", "Commune"),
    ):
        cell = sheet["{0}{1}".format(column, row)]
        cell.value = label
        cell.font = styles["section"]
        cell.fill = styles["band"]
    row += 1
    for station in stations:
        sheet["A{0}".format(row)] = station["code"]
        sheet["B{0}".format(row)] = station["nom"]
        sheet["C{0}".format(row)] = station["capacite_eh"]
        sheet["D{0}".format(row)] = station["charge_max_eh"]
        sheet["E{0}".format(row)] = station["taux_charge_pct"]
        sheet["E{0}".format(row)].number_format = "0.0"
        sheet["F{0}".format(row)] = station["nature"]
        sheet["G{0}".format(row)] = (
            "oui" if station["en_service"] else "non"
        )
        zone_sensible = station["zone_sensible"]
        sheet["H{0}".format(row)] = (
            "non renseigné" if zone_sensible is None else
            ("oui" if zone_sensible else "non")
        )
        sheet["I{0}".format(row)] = station["nom_zone_sensible"]
        sheet["J{0}".format(row)] = station["autosurveillance"]
        sheet["K{0}".format(row)] = station["conformite_autosurv"]
        sheet["L{0}".format(row)] = station["commune"]
        for column in "ABCDEFGHIJKL":
            sheet["{0}{1}".format(column, row)].border = styles["rule"]
        row += 1

    return row + 1


def _block_prelevements(sheet, row, prelevements, styles):
    """Releve des ouvrages de prelevement d'eau (Hub'Eau / BNPE)."""
    ouvrages = (prelevements or {}).get("ouvrages") or []
    if not ouvrages:
        return row
    row = _title_row(sheet, row, "Prélèvements d'eau", styles)
    row = _header_row(sheet, row, ("Code", "Ouvrage", "Volume (m³/an)",
                                   "Année", "Commune", "Usage"), styles)
    for ouvrage in ouvrages:
        row = _data_row(sheet, row, (
            ouvrage["code"], ouvrage["nom"] or ouvrage["code"],
            ouvrage["volume_m3"], ouvrage["annee"], ouvrage["commune"],
            ouvrage["usage"],
        ), styles, {3: "#,##0"})
    return row + 1


def _block_sites(sheet, row, pressions, styles):
    """Sols pollues et etablissements declarant leurs rejets (Georisques)."""
    from ..core.pressions import INVENTAIRES

    for key, _layer, label in INVENTAIRES:
        inventaire = (pressions or {}).get(key)
        if inventaire is None:
            continue
        row = _title_row(sheet, row, "{0} : {1}".format(
            label, inventaire["nb"]), styles)
        sites = inventaire.get("sites") or []
        if not sites:
            row += 1
            continue
        row = _header_row(sheet, row, (
            "Code", "Établissement ou site",
            "Surface (ha)" if key == "sis" else None, "Commune", None,
            "Code d'activité" if key == "irep" else "État ou statut",
            "Fiche"), styles)
        for site in sites:
            row = _data_row(sheet, row, (
                site["code"], site["nom"], site["surface_ha"],
                site["commune"], None, site["etat"], site["fiche"],
            ), styles, {3: "0.00"})
        row += 1
    return row


def _sheet_pressions(book, steu, population, values, prelevements,
                     pressions, styles):
    """Pression anthropique : STEU, prelevements et sols pollues, comme la
    section du rapport PDF."""
    has_sites = any((pressions or {}).get(key) is not None
                    for key in ("basias", "basol", "sis", "irep"))
    if not ((steu or {}).get("stations")
            or (prelevements or {}).get("ouvrages") or has_sites
            or (population or {}).get("population_estimee") is not None):
        return
    sheet = _theme_sheet(book, "Pression anthropique", (
        16, 40, 16, 18, 16, 30, 12, 14, 24, 18, 22, 20))
    row = 1
    row = _block_population(sheet, row, population, styles, steu, values)
    row = _block_steu(sheet, row, steu, styles)
    row = _block_prelevements(sheet, row, prelevements, styles)
    row = _block_sites(sheet, row, pressions, styles)
    _setup_a4(sheet, row, "L")


def _sheet_water(book, result, structures, prelevements, styles):
    """Masses d'eau, SAGE, Vigicrues, eau potable et sites hydrometriques."""
    body = result.get("water_body") or {}
    meso = result.get("groundwater") or {}
    her = result.get("hydroecoregion") or {}
    gestion = result.get("gestion_eau") or {}
    sage = gestion.get("sage") or {}
    vigi = gestion.get("vigicrues") or {}
    hydro = (structures or {}).get("hydrometrie") or {}
    prelevements = prelevements or {}
    if not (body or meso or any(her.values()) or sage or vigi
            or hydro.get("sites") or prelevements.get("nb_aep")):
        return
    sheet = _theme_sheet(book, "Eau", (16, 52, 18, 18, 16))
    row = 1
    if body or meso or any(her.values()):
        row = _title_row(sheet, row, "Masses d'eau et hydroécorégion", styles)
        for label, value in (
            ("Masse d'eau de surface — code européen", body.get("code_eu")),
            ("Masse d'eau de surface — bassin versant", body.get("nom_bv")),
            ("Masse d'eau souterraine — code européen", meso.get("code_eu")),
            ("Masse d'eau souterraine — dénomination", meso.get("nom")),
            ("Hydroécorégion de niveau 1", her.get("her1_nom")),
            ("Hydroécorégion de niveau 2", her.get("her2_nom")),
        ):
            if value not in (None, ""):
                row = _pair_row(sheet, row, label, value)
        row += 1
    if sage:
        row = _title_row(sheet, row, "SAGE", styles)
        if not sage.get("nb"):
            row = _pair_row(sheet, row, "Aucun SAGE ne couvre le bassin", None)
        else:
            row = _header_row(sheet, row, ("Code", "SAGE",
                                           "État d'avancement",
                                           "Surface (ha)",
                                           "Part (% du bassin)"), styles)
            for item in sage.get("sages") or ():
                row = _data_row(sheet, row, (item["code"], item["nom"],
                                             item["etat"], item["surface_ha"],
                                             item["part_pct"]),
                                styles, {4: "0.00", 5: "0.0"})
        row += 1
    if vigi:
        row = _title_row(sheet, row, "Surveillance des crues (Vigicrues)",
                         styles)
        row = _pair_row(sheet, row, "Cours d'eau surveillés (km)",
                        vigi.get("longueur_km"), "0.0")
        row = _pair_row(sheet, row, "Stations Vigicrues",
                        vigi.get("nb_stations"), "0")
        if vigi.get("troncons"):
            row = _header_row(sheet, row, ("Code", "Tronçon surveillé",
                                           "Longueur (km)"), styles)
            for item in vigi["troncons"]:
                row = _data_row(sheet, row, (item["code"], item["nom"],
                                             item["longueur_km"]),
                                styles, {3: "0.0"})
        if vigi.get("stations"):
            row = _header_row(sheet, row, ("Code", "Station Vigicrues",
                                           "Cours d'eau"), styles)
            for item in vigi["stations"]:
                row = _data_row(sheet, row, (item["code"], item["nom"],
                                             item["cours_d_eau"]), styles)
        row += 1
    if prelevements.get("nb_aep"):
        row = _title_row(sheet, row, "Eau potable", styles)
        row = _pair_row(sheet, row,
                        "Ouvrages de prélèvement pour l'eau potable",
                        prelevements.get("nb_aep"), "0")
        row = _pair_row(sheet, row, "Volume prélevé (m³/an)",
                        prelevements.get("volume_aep_m3"), "#,##0")
        row += 1
    if hydro.get("sites"):
        row = _title_row(sheet, row, "Sites hydrométriques", styles)
        row = _header_row(sheet, row, ("Code Sandre", "Site", "Type",
                                       "Gestionnaire"), styles)
        for site in hydro["sites"]:
            row = _data_row(sheet, row, (site["code"], site["nom"],
                                         site["type"], site["gestionnaire"]),
                            styles)
    _setup_a4(sheet, row, "E")


# (theme, jeu de donnees, fournisseur et service, couche ou reference
# technique) - une ligne par jeu de donnees que le pipeline peut interroger,
# qu'il ait ete demande ou non sur ce bassin precis. Reprise a l'identique de
# report.layout : le classeur ne peut pas l'importer de la, ce module devant
# rester utilisable sans QGIS (voir l'en-tete du fichier), mais les deux
# doivent rester d'accord, ce que tools/check_fields verifie.
SOURCES = (
    ("Relief", "MNT RGE ALTI, maille 5 m",
     "IGN — Géoplateforme, WMS (BIL 32 bits)",
     "ELEVATION.ELEVATIONGRIDCOVERAGE.HIGHRES"),
    ("Hydrographie", "Tronçons et bassins versants topographiques BD TOPO",
     "IGN — Géoplateforme, WFS",
     "BDTOPO_V3:troncon_hydrographique, bassin_versant_topographique"),
    ("Hydrographie", "Obstacles à l'écoulement (ROE)",
     "Sandre (eaufrance) — WFS 1.1", "sa:ObstEcoul"),
    ("Hydrographie", "Sites hydrométriques",
     "Sandre (eaufrance) — WFS 1.1", "sa:SiteHydro"),
    ("Hydrographie", "Stations de traitement des eaux usées (STEU)",
     "Sandre (eaufrance) — WFS 1.1", "sa:SysTraitementEauxUsees"),
    ("Occupation du sol", "Bâti et zones d'habitation BD TOPO",
     "IGN — Géoplateforme, WFS",
     "BDTOPO_V3:batiment, BDTOPO_V3:zone_d_habitation"),
    ("Occupation du sol", "Formations forestières BD Forêt v2",
     "IGN — Géoplateforme, WFS",
     "LANDCOVER.FORESTINVENTORY.V2:formation_vegetale"),
    ("Occupation du sol", "Corine Land Cover 2018",
     "Géoplateforme, WFS", "LANDCOVER.CLC18_FR:clc18_fr"),
    ("Agriculture (PAC)", "RPG — parcelles et codes cultures",
     "ASP/IGN — Géoplateforme, WFS",
     "RPG.LATEST:parcelles_graphiques, RPG.LATEST:codes_cultures"),
    ("Agriculture (PAC)", "RPG catégorisé — bio et conversion, millésime 2024",
     "Géoplateforme, WFS",
     "RPG_PARCELLES-CATEGORISEES_2024"),
    ("Agriculture (PAC)", "Prairies sensibles BCAE",
     "Géoplateforme, WFS", "PRAIRIES.SENSIBLES.BCAE:prairies_sensibles"),
    ("Agriculture (PAC)", "Aires AOC viticoles",
     "Géoplateforme, WFS", "AOC-VITICOLES:aire_parcellaire"),
    ("Zonages environnementaux",
     "ZNIEFF I et II, ZSC, ZPS, arrêté de protection de biotope, réserves "
     "naturelles nationale et régionale, parc naturel régional, Ramsar, "
     "conservatoires d'espaces naturels, cœurs de parc national, réserves "
     "biologiques, réserves de biosphère, arrêtés de protection d'habitat",
     "INPN / Patrinat — Géoplateforme, WFS",
     "patrinat_znieff1, patrinat_znieff2, patrinat_sic, patrinat_zps, "
     "patrinat_apb, patrinat_rnn, patrinat_rnr, patrinat_pnr, "
     "patrinat_ramsar, patrinat_cen, patrinat_pn, patrinat_rb, "
     "patrinat_bios, patrinat_aphn"),
    ("Zonages environnementaux", "Zones humides et tourbières BCAE",
     "Géoplateforme, WFS", "TOURBIERES_ZONES-HUMIDES.BCAE:bcae"),
    ("Masses d'eau", "Masse d'eau de surface et bassin versant spécifique",
     "Sandre (eaufrance) — WFS 1.1",
     "sa:MasseDEauRiviere_VRAP2022_FXX, "
     "sa:BVSpeMasseDEauSurface_VEDL2019_FXX"),
    ("Masses d'eau", "Masse d'eau souterraine",
     "Sandre (eaufrance) — WFS 1.1", "sa:MasseDEauSouterraine_VEDL2019_FXX"),
    ("Masses d'eau", "Hydroécorégions de niveau 1 et 2",
     "Sandre (eaufrance) — WFS 1.1",
     "sa:Hydroecoregion1_FXX, sa:Hydroecoregion2_FXX"),
    ("Population", "Logements du bâti (nombre_de_logements)",
     "IGN — Géoplateforme, WFS", "BDTOPO_V3:batiment"),
    ("Population", "Communes et population officielle",
     "IGN — Géoplateforme, WFS", "ADMINEXPRESS-COG.LATEST:commune"),
    ("Hydrographie", "Prélèvements d'eau (BNPE)",
     "Hub'Eau — API REST (Office français de la biodiversité)",
     "prelevements/chroniques"),
    ("Occupation du sol", "Habitats CarHab — physionomie et humidité du sol",
     "PatriNat / IGN / OFB — Géoplateforme, WFS",
     "Carhab_habitat:habitats_carhab"),
    ("Agriculture et paysage", "Haies — dispositif de suivi des bocages",
     "IGN / OFB — Géoplateforme, WFS", "HAIES.BOCAGES:haie"),
    ("Agriculture et paysage", "Forêts publiques relevant du régime forestier",
     "ONF — Géoplateforme, WFS", "ONF.FORETS_PUBLIQUES:ONF_FORETS_PUBLIQUES"),
    ("Zonages environnementaux",
     "Mesures compensatoires des atteintes à la biodiversité",
     "Géoplateforme, WFS", "MESURES_COMPENSATOIRES:emprises_polygones"),
    ("Zonages environnementaux", "Zones humides d'importance majeure",
     "Réseau partenarial des données sur les zones humides — WFS 1.1",
     "ZHIM"),
    ("Biodiversité", "Observations d'espèces, comptes par grand groupe",
     "GBIF — API REST", "occurrence/search"),
    ("Gestion de l'eau", "Périmètres des SAGE",
     "Sandre (eaufrance) — WFS 1.1", "sa:Sage_FXX"),
    ("Gestion de l'eau", "Vigicrues — tronçons surveillés et stations",
     "SCHAPI — Géoplateforme, WFS", "VIGICRUES:troncons, VIGICRUES:stations"),
    ("Pression anthropique",
     "Anciens sites industriels (BASIAS) et sites pollués (BASOL)",
     "Géorisques (BRGM) — WFS", "SSP_ETS_GE_POINT, SSP_INSTR_GE_POINT"),
    ("Pression anthropique", "Secteurs d'information sur les sols (SIS)",
     "Géorisques (BRGM) — WFS", "SSP_CLASSIF_SIS_GE"),
    ("Pression anthropique", "Registre des émissions polluantes (IREP)",
     "Géorisques — WFS", "ETABLISSEMENTS_POLLUEURS"),
    ("Fond de carte", "Plan IGN v2",
     "IGN — Géoplateforme, WMTS", "GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2"),
)


def _sheet_sources(book, styles):
    """Origine de chaque jeu de donnees et methode, derniere feuille."""
    sheet = book.create_sheet("Sources et méthode")
    sheet.sheet_view.showGridLines = False
    for column, width in (("A", 24), ("B", 46), ("C", 34), ("D", 46)):
        sheet.column_dimensions[column].width = width

    row = 1
    for column, label in (("A", "Thème"), ("B", "Jeu de données"),
                          ("C", "Fournisseur / service"),
                          ("D", "Couche ou référence technique")):
        cell = sheet["{0}{1}".format(column, row)]
        cell.value = label
        cell.font = styles["section"]
        cell.fill = styles["band"]
    row += 1
    for theme, dataset, provider, layer_ref in SOURCES:
        sheet["A{0}".format(row)] = theme
        sheet["B{0}".format(row)] = dataset
        sheet["C{0}".format(row)] = provider
        sheet["D{0}".format(row)] = layer_ref
        for column in "ABCD":
            cell = sheet["{0}{1}".format(column, row)]
            cell.border = styles["rule"]
            cell.alignment = styles["left"]
        row += 1
    row += 1

    sheet["A{0}".format(row)] = (
        "Les normes de rejet des stations de traitement (STEU) ne sont pas "
        "rapatriées : n'existant nulle part en donnée ouverte station par "
        "station, elles sont calculées à partir de la capacité et de la "
        "zone sensible de chaque station, d'après l'arrêté du 21 juillet "
        "2015 relatif aux systèmes d'assainissement collectif. L'arrêté "
        "préfectoral propre à chaque ouvrage peut être plus strict, jamais "
        "plus permissif."
    )
    sheet["A{0}".format(row)].font = styles["footer"]
    sheet["A{0}".format(row)].alignment = styles["left"]
    sheet.row_dimensions[row].height = 42
    row += 2

    sheet["A{0}".format(row)] = (
        "La population du bassin, quand elle figure dans l'onglet Pression anthropique, "
        "est une estimation et non un recensement. Pour chaque commune "
        "recoupant le bassin : le nombre de logements du bâti BD TOPO dans "
        "la part de la commune comprise dans le bassin est rapporté au "
        "nombre de logements de la commune entière ; cette part est "
        "appliquée à la population officielle de la commune (attribut "
        "ADMIN EXPRESS COG). Les logements comptent, non les bâtiments : un "
        "garage ou un hangar agricole porte zéro logement, l'IGN le "
        "calculant à partir des seules parties d'évaluation cadastrale "
        "marquées habitation, ce qui évite de surestimer la population par "
        "le bâti annexe. La méthode suppose la densité de logements "
        "comparable dans et hors bassin, hypothèse fragile près d'un "
        "bourg-centre à cheval sur la limite communale."
    )
    sheet["A{0}".format(row)].font = styles["footer"]
    sheet["A{0}".format(row)].alignment = styles["left"]
    sheet.row_dimensions[row].height = 56
    row += 2

    sheet["A{0}".format(row)] = (
        "Les prélèvements d'eau ne mesurent que ce qu'Hub'Eau publie : le "
        "service ne filtre pas par emprise géographique, seulement par "
        "commune, si bien que le relevé part des communes qui recoupent le "
        "bassin puis ne garde que les ouvrages dont le point tombe "
        "réellement dedans. Chaque ouvrage porte plusieurs années "
        "déclarées ; seule la plus récente connue est retenue, qui peut "
        "dater de plusieurs années selon l'ouvrage — l'année retenue "
        "figure sur chaque ligne du relevé, onglet Pression anthropique."
    )
    sheet["A{0}".format(row)].font = styles["footer"]
    sheet["A{0}".format(row)].alignment = styles["left"]
    sheet.row_dimensions[row].height = 42

    _setup_a4(sheet, row, "D")


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
        sheet["B{0}".format(row)].number_format = "#,##0.0"
        for column in "AB":
            sheet["{0}{1}".format(column, row)].border = styles["rule"]
        total += length
        row += 1

    sheet["A{0}".format(row + 1)] = "Linéaire total (m)"
    sheet["A{0}".format(row + 1)].font = styles["value"]
    sheet["B{0}".format(row + 1)] = total
    sheet["B{0}".format(row + 1)].number_format = "#,##0.0"
    sheet["B{0}".format(row + 1)].font = styles["value"]
    _setup_a4(sheet, row + 1)
