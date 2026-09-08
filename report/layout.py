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
           color=ARDOISE, align_right=False, page=0):
    item = QgsLayoutItemLabel(layout)
    item.setText(text)
    item.setTextFormat(_text_format(size, bold, color))
    # attemptMove prend le numero de page en dernier argument, et y devient
    # alors une ordonnee dans cette page. Sans lui, il faudrait ajouter la
    # hauteur des pages precedentes a chaque coordonnee, et toute la mise en
    # page de la premiere page serait a relire pour comprendre la seconde.
    item.attemptMove(QgsLayoutPoint(x, y, MM), True, False, page)
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
                 subtitle=None, details=None):
    """Monte la mise en page et renvoie (layout, couches temporaires).

    Les couches temporaires (masque, fond de plan) doivent rester vivantes
    jusqu'a l'export : elles sont renvoyees pour que l'appelant les garde.

    details porte le detail des zonages et de l'eau - ce que la table du
    bassin ne peut pas contenir parce qu'il s'agit de listes : les sites de
    chaque zonage, les ouvrages du ROE, les stations. Il commande la seconde
    page, qui n'est ajoutee que s'il y a de quoi la remplir.
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
    # Les zonages passent au-dessus du bassin et sous le reseau : leurs aplats
    # translucides se liraient mal a travers le bleu du bassin, et ils
    # masqueraient le chevelu s'ils passaient par-dessus. Ils sont deja
    # decoupes sur le bassin, le voile exterieur ne les concerne donc pas.
    if layers.get("zonages") is not None:
        stack.insert(0, layers["zonages"])
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

    _zonage_legend(layout, map_item, layers.get("zonages"), project)

    scale = QgsLayoutItemScaleBar(layout)
    scale.setStyle("Single Box")
    scale.setLinkedMap(map_item)
    scale.applyDefaultSize()
    scale.setTextFormat(_text_format(7.0))
    scale.attemptMove(QgsLayoutPoint(MARGIN + 3, 136, MM))
    layout.addLayoutItem(scale)

    # ---------------------------------------- Informations, moitie basse
    restantes = _fill_bottom(layout, values, charts_paths)

    # ------------------------------------------------------------ Pied
    # La ligne des sources s'arrete avant la mention de droite : depuis que
    # les zonages et les referentiels Sandre s'y ajoutent, elle occuperait
    # toute la largeur et viendrait se poser sur "Produit par BVLIP". Deux
    # lignes en dessous de la marge valent mieux qu'un chevauchement.
    _label(layout,
           "Sources : RGE ALTI, BD TOPO et BD Forêt v2 (IGN) · Corine Land "
           "Cover 2018 · zonages INPN / Patrinat · masses d'eau, "
           "hydroécorégions, ROE et STEU (Sandre) · prélèvements (Hub'Eau) · "
           "fond Plan IGN v2",
           MARGIN, A4_HEIGHT - 15, A4_WIDTH - 2 * MARGIN - 34, 9,
           size=6.5, color=GRIS)
    _label(layout, "Produit par BVLIP", A4_WIDTH - MARGIN - 32,
           A4_HEIGHT - 12, 32, 5, size=6.5, color=GRIS, align_right=True)

    # ------------------------------------------- Pages de detail, si utile
    #
    # Le pied de page des pages de detail n'est pose qu'une fois la page des
    # sources ajoutee : son "Page X sur Y" annonce un total, et ce total
    # n'est vrai que si plus aucune page ne vient s'ajouter derriere.
    detail_pages = _build_details_page(
        layout, details, title, restantes, values,
        context={
            "project": project, "basin": basin, "mask": mask,
            "basemap": base,
            "foret": layers.get("foret"),
            "parcelles": layers.get("parcelles"),
            "zonages": layers.get("zonages"),
            "obstacles": layers.get("obstacles"),
            "steu": layers.get("steu"),
            "prelevements": layers.get("prelevements"),
            "reseau": layers.get("reseau"),
        },
    )
    _build_sources_page(layout, title)
    if detail_pages:
        _details_footers(layout, detail_pages)

    return layout, temporary


# ------------------------------------------------ Seconde page : le detail
#
# La premiere page ne bouge pas : c'est la fiche du bassin, et elle doit
# rester comparable d'un bassin a l'autre. Tout ce qui est de longueur
# variable - les sites d'un zonage, les ouvrages du ROE, les stations - vient
# ici, ou la place manque moins et ou une liste vide ne laisse pas de trou
# dans une mise en page reglee au millimetre.

PAGE2_TOP = 26.0            # sous le titre de la page
PAGE2_BOTTOM = A4_HEIGHT - 14.0
ROW = 3.5                   # hauteur d'une ligne de tableau
SECTION_GAP = 5.5           # avant un titre de section
HEADER_GAP = 4.2            # apres une ligne d'en-tetes de colonnes

# Largeur moyenne d'un caractere a 6,4 points, en millimetres. Elle ne sert
# plus qu'en dernier recours, quand les metriques de police sont indisponibles
# - un poste sans serveur graphique, par exemple. Volontairement large : une
# ligne de trop laisse un blanc, une ligne de moins fait un recouvrement.
CHAR_WIDTH = 1.45

# Taille du texte des tableaux de detail, en points.
CELL_SIZE = 6.4

# Notes de methode : un peu plus petit que les tableaux, et un interligne un
# peu plus serre. C'est du texte suivi et non des lignes a comparer d'un
# tableau a l'autre, il se lit en continu.
NOTE_SIZE = 6.0
NOTE_ROW = 2.9

# Facteur d'agrandissement de la mesure. Police et colonne sont grossies
# ensemble : le rapport des deux ne change pas, la precision si.
#
# A 6,4 points, une police fait huit pixels et demi de haut, et le moteur
# arrondit l'avance de chaque caractere au pixel. L'erreur s'accumule d'une
# lettre a l'autre et gonfle la mesure de cinq pour cent - assez pour croire
# qu'un libelle deborde alors qu'il tient. Releve : "Gites a chauves-souris,
# Contreforts et Montagne Bourbonnaise" mesurait 1,054 fois sa colonne et
# rendait pourtant une seule ligne, laissant une ligne blanche dans le
# tableau. Mesure faite dix fois plus grande, l'arrondi devient negligeable :
# le meme libelle tombe a 0,950, et le premier vrai deux-lignes a 1,123.
MEASURE_SCALE = 10.0


def _wrapped_lines(text, width, size=CELL_SIZE, bold=False):
    """Nombre de lignes qu'occupera ce texte dans cette largeur.

    Mesure par les metriques de la police, et non estimee au caractere. Une
    moyenne ne peut pas convenir ici : dans une colonne de 68 mm, cinquante-
    deux caracteres de bas de casse tiennent sur une ligne quand quarante-huit
    capitales n'y tiennent deja plus. Une estimation juste en moyenne se
    trompe donc dans les deux sens, et se tromper vers le bas fait recouvrir
    la rangee suivante - le defaut qu'on repare ici.

    Le calcul passe par le retour a la ligne de Qt, celui-la meme qui
    s'appliquera au rendu : les mots ne sont pas coupes, et une colonne etroite
    ne rend pas un nombre de lignes fantaisiste.
    """
    text = str(text)
    if not text:
        return 1
    try:
        from qgis.PyQt.QtCore import Qt
        from qgis.PyQt.QtGui import QFontMetricsF, QGuiApplication

        screen = QGuiApplication.primaryScreen()
        dpi = (screen.logicalDotsPerInchX() if screen else 0.0) or 96.0
        font = QFont("Arial")
        font.setBold(bold)
        font.setPointSizeF(size * MEASURE_SCALE)
        metrics = QFontMetricsF(font)
        # La largeur passe en pixels de police, les deux grandeurs etant
        # ramenees au meme repere : le rapport texte/colonne ne depend alors
        # plus de la resolution du poste.
        box = QRectF(0.0, 0.0, width * MEASURE_SCALE * dpi / 25.4, 100000.0)
        wrapped = metrics.boundingRect(
            box, int(Qt.TextFlag.TextWordWrap), text)
        spacing = metrics.lineSpacing() or 1.0
        return max(1, int(round(wrapped.height() / spacing)))
    except Exception:      # pragma: no cover - poste sans police disponible
        per_line = max(1, int(width / CHAR_WIDTH))
        return max(1, -(-len(text) // per_line))

# Colonnes du tableau des zonages, en millimetres depuis la marge gauche.
# (decalage, largeur, aligne a droite)
ZONAGE_COLUMNS = (
    (0.0, 46.0, False),      # zonage
    (47.0, 68.0, False),     # site
    (116.0, 28.0, False),    # code INPN ou Sandre
    (145.0, 22.0, True),     # surface dans le bassin
    (168.0, 18.0, True),     # part du bassin
)

# Colonnes du tableau des obstacles a l'ecoulement.
ROE_COLUMNS = (
    (0.0, 22.0, False),      # code ROE
    (23.0, 68.0, False),     # nom de l'ouvrage
    (92.0, 26.0, False),     # type Sandre
    (119.0, 20.0, True),     # chute
    (140.0, 18.0, False),    # provenance de la chute
    (159.0, 27.0, False),    # passe a poissons
)

# Colonnes du tableau Corine Land Cover, niveau 3.
CLC_COLUMNS = (
    (0.0, 14.0, False),      # code CLC
    (16.0, 106.0, False),    # libelle de la classe
    (124.0, 30.0, True),     # surface
    (156.0, 30.0, True),     # part du bassin
)

# Colonnes des tableaux agricoles : categories de culture, puis cultures
# detaillees avec leur code.
AGRI_COLUMNS = (
    (0.0, 120.0, False),
    (122.0, 30.0, True),
    (154.0, 32.0, True),
)
CULTURE_COLUMNS = (
    (0.0, 14.0, False),
    (16.0, 106.0, False),
    (124.0, 30.0, True),
    (156.0, 30.0, True),
)

# Colonnes du tableau des formations de la BD Foret.
FOREST_COLUMNS = (
    (0.0, 120.0, False),
    (122.0, 30.0, True),
    (154.0, 32.0, True),
)

# Colonnes du tableau des stations hydrometriques.
HYDRO_COLUMNS = (
    (0.0, 26.0, False),
    (27.0, 84.0, False),
    (112.0, 74.0, False),
)

STEU_COLUMNS = (
    (0.0, 18.0, False),      # code Sandre
    (19.0, 56.0, False),     # nom de la station
    (76.0, 22.0, True),      # capacite nominale (EH)
    (99.0, 20.0, True),      # taux de charge (%)
    (120.0, 41.0, False),    # commune
    (162.0, 24.0, False),    # autosurveillance
)

PRELEVEMENT_COLUMNS = (
    (0.0, 60.0, False),      # nom de l'ouvrage
    (61.0, 55.0, False),     # usage
    (117.0, 25.0, True),     # volume (m3/an)
    (144.0, 20.0, True),     # annee
    (166.0, 20.0, False),    # commune
)


class _Cursor:
    """Curseur d'ecriture sur les pages de detail, qu'il cree au besoin.

    Il tient l'ordonnee courante et, quand la place manque, ouvre une page de
    plus et continue. Rien n'est tronque : un bassin qui porte deux cents
    ouvrages du ROE et trente sites de zonage sort autant de pages qu'il en
    faut, la ou un rapport tronque laisserait croire qu'on a tout vu.

    Trois soins accompagnent la coupure, faute de quoi la lecture se perd
    d'une page a l'autre :

      - les en-tetes de colonnes sont redessines en tete de page, suivis de
        "(suite)", parce qu'un tableau qui reprend sans ses intitules ne se
        lit plus ;
      - un titre de section ne reste jamais seul en bas de page : s'il ne
        peut pas etre suivi d'au moins deux lignes, il passe a la page
        suivante avec elles ;
      - une paire intitule/valeur ne se coupe pas en son milieu, sa hauteur
        etant calculee avant de la poser.
    """

    def __init__(self, layout, page, title, heading=None):
        self.layout = layout
        self.page = page
        self.title = title
        # DETAILS_TITLE n'existe pas encore a la definition de cette classe,
        # placee plus haut dans le fichier pour rester pres de _Cursor.row -
        # d'ou la resolution paresseuse, au premier appel et non au chargement
        # du module.
        self.heading = heading if heading is not None else DETAILS_TITLE
        self.pages = [page]
        self.y = PAGE2_TOP
        # En-tetes a redessiner en haut de la page suivante. Remis a None des
        # qu'une section s'acheve : un tableau termine n'a pas a reapparaitre.
        self._repeat = None

    # -------------------------------------------------------- pagination

    def _add_page(self):
        from qgis.core import QgsLayoutItemPage

        page_item = QgsLayoutItemPage(self.layout)
        page_item.setPageSize(QgsLayoutSize(A4_WIDTH, A4_HEIGHT, MM))
        self.layout.pageCollection().addPage(page_item)
        self.page = self.layout.pageCollection().pageCount() - 1
        self.pages.append(self.page)
        _details_header(self.layout, self.page, self.title, first=False,
                        heading=self.heading)
        self.y = PAGE2_TOP
        if self._repeat is not None:
            spec, headers = self._repeat
            self._draw_columns(spec, headers, suite=True)

    def ensure(self, height):
        """Garantit la place demandee, en ouvrant une page s'il le faut."""
        if self.y + height > PAGE2_BOTTOM:
            self._add_page()

    def starts_page(self, height):
        """La prochaine ecriture de cette hauteur ouvrira-t-elle une page ?

        Sert a rappeler en tete de page ce qu'une ligne aurait tu : le nom
        d'un zonage n'est porte que par la premiere de ses lignes, et une
        page qui commencerait au milieu de ses sites ne dirait pas desquels
        il s'agit.
        """
        return self.y + height > PAGE2_BOTTOM

    # ------------------------------------------------------------ ecriture

    def new_page(self):
        """Ouvre une page, sauf si l'on est deja en haut d'une page vierge.

        Le garde evite la page blanche : demander un saut alors qu'on vient
        d'en ouvrir une en produirait une vide, entre deux sections qui se
        suivent chacune sur sa propre page.
        """
        if self.y > PAGE2_TOP:
            self._add_page()

    def section(self, title, reserve=0.0, page_break=False):
        """Titre de section.

        reserve dit la hauteur du premier bloc a venir, quand il est plus haut
        que deux lignes : une section qui s'ouvre sur une carte de soixante-
        seize millimetres laisserait sinon son titre seul en bas de page, la
        carte partant a la suivante.

        page_break ouvre une page pour la section. Les trois sections qui
        portent une carte en profitent : une carte, sa legende et ses tableaux
        remplissent une page a eux seuls, et les faire commencer au milieu de
        la precedente ne gagnerait que quelques lignes en coupant la carte de
        ce qu'elle illustre.
        """
        self._repeat = None
        if page_break:
            self.new_page()
        self.ensure(SECTION_GAP + 6.0 + max(2 * ROW, reserve))
        self.y += SECTION_GAP
        _label(self.layout, title, MARGIN, self.y, 186, 5,
               size=9.5, bold=True, page=self.page)
        self.y += 6.0

    def columns(self, spec, headers):
        self.ensure(HEADER_GAP + 2 * ROW)
        self._repeat = (spec, headers)
        self._draw_columns(spec, headers)

    def _draw_columns(self, spec, headers, suite=False):
        for index, ((offset, width, right), text) in enumerate(
                zip(spec, headers)):
            if suite and index == 0:
                text = "{0} (suite)".format(text)
            _label(self.layout, text, MARGIN + offset, self.y, width, ROW,
                   size=6.0, bold=True, color=GRIS, align_right=right,
                   page=self.page)
        self.y += HEADER_GAP

    def row(self, spec, cells, bold=False):
        """Une rangee de tableau, aussi haute que sa cellule la plus longue.

        Une hauteur figee etait le defaut : un nom de site plus long que sa
        colonne - "TOURBIERES DE LA CROIX DE L'OLIVIER ET DU PLAN DE
        LAMOUSSIERE, SECTEUR AUVERGNE" tient en soixante-dix-huit caracteres
        pour une colonne qui en loge cinquante - passait a la ligne et venait
        se poser sur la rangee suivante. La hauteur se mesure donc avant de
        poser quoi que ce soit, et toutes les cellules la partagent.
        """
        lines = 1
        for (offset, width, _right), text in zip(spec, cells):
            if text in (None, ""):
                continue
            lines = max(lines, _wrapped_lines(text, width, bold=bold))
        height = lines * ROW
        self.ensure(height)
        for (offset, width, right), text in zip(spec, cells):
            if text in (None, ""):
                continue
            _label(self.layout, str(text), MARGIN + offset, self.y, width,
                   height, size=CELL_SIZE, bold=bold, align_right=right,
                   page=self.page)
        self.y += height

    def pair(self, label, value, width=96.0):
        """Un intitule a gauche, sa valeur a droite.

        La valeur peut etre longue - la denomination d'une masse d'eau tient
        en quatre-vingts caracteres - et Qt la renvoie alors a la ligne dans
        un cadre haut d'une seule ligne : le debordement vient recouvrir la
        paire suivante. On compte donc les lignes a l'avance, a partir de la
        largeur disponible, et on avance le curseur d'autant.
        """
        value_width = 186 - width - 2
        text = str(value)
        # L'intitule est mesure lui aussi : certains tiennent sur deux lignes
        # dans leur colonne, et la valeur ne doit pas s'en trouver decalee.
        height = ROW * max(_wrapped_lines(text, value_width, bold=True),
                           _wrapped_lines(label, width))
        # La hauteur est connue avant de poser quoi que ce soit : une paire
        # de deux lignes ne se coupe donc jamais entre ses deux lignes.
        self.ensure(height)
        _label(self.layout, label, MARGIN, self.y, width, height,
               size=CELL_SIZE, page=self.page)
        _label(self.layout, text, MARGIN + width + 2, self.y,
               value_width, height, size=CELL_SIZE, bold=True,
               page=self.page)
        self.y += height

    def note(self, text):
        self.ensure(ROW)
        _label(self.layout, text, MARGIN, self.y, 186, ROW, size=6.0,
               color=GRIS, page=self.page)
        self.y += ROW

    def paragraph(self, text, size=NOTE_SIZE, color=GRIS):
        """Un texte suivi, sur toute la largeur de la page.

        Sert aux notes de methode : ce qu'un tableau ne peut pas dire, comme
        pourquoi deux sources donnent deux chiffres differents pour ce qui
        ressemble a la meme chose. Sa hauteur est mesuree avant d'etre posee,
        comme celle d'une rangee, et il ne se coupe pas d'une page a l'autre -
        une explication scindee en deux n'explique plus rien.
        """
        lines = _wrapped_lines(text, 186.0, size=size)
        height = lines * NOTE_ROW
        self.ensure(height)
        _label(self.layout, text, MARGIN, self.y, 186, height, size=size,
               color=color, page=self.page)
        self.y += height


def _number(value, decimals=2):
    """Nombre a la francaise, espace insecable en separateur de milliers."""
    if value is None:
        return ""
    if abs(value) >= 1000:
        return "{:,.0f}".format(value).replace(",", " ")
    return ("{:." + str(decimals) + "f}").format(value)


def _yes_no(value):
    if value is None:
        return "non renseigné"
    return "oui" if value else "non"


def _has_details(details):
    """Y a-t-il de quoi remplir une page de detail ?"""
    if not details:
        return False
    protected = details.get("protected") or {}
    structures = details.get("structures") or {}
    cover = details.get("land_cover") or {}
    agri = details.get("agriculture") or {}
    return bool(
        (protected.get("zonages") or [])
        or (structures.get("roe") or {}).get("nb")
        or (structures.get("hydrometrie") or {}).get("nb")
        or (details.get("steu") or {}).get("nb")
        or (details.get("prelevements") or {}).get("nb")
        or details.get("water_body") or details.get("groundwater")
        or any((details.get("hydroecoregion") or {}).values())
        or (cover.get("corine") or {}).get("classes")
        or (cover.get("foret") or {}).get("formations")
        or cover.get("bati")
        or (agri.get("rpg") or {}).get("nb_parcelles")
        or (agri.get("prairies") or {}).get("nb")
        or (agri.get("aoc") or {}).get("nb")
    )


# Carte thematique en tete de section : largeur de la carte, de la legende, et
# hauteur du bloc. La legende se pose a droite, dans ce qui reste des 186 mm.
SECTION_MAP_WIDTH = 104.0
SECTION_MAP_HEIGHT = 76.0
SECTION_LEGEND_WIDTH = 186.0 - SECTION_MAP_WIDTH - 4.0

# Au-dela de ce nombre d'entrees, la legende ne tient plus dans la colonne de
# droite : les dix-sept cultures declarees d'un bassin d'elevage y descendent
# plus bas que la carte. Elle passe alors sous la carte, sur toute la largeur
# et sur deux colonnes, et la carte prend la largeur entiere.
LEGEND_SIDE_MAX = 10
LEGEND_COLUMNS = 2

# Hauteur d'une ligne de legende et de son titre, pour reserver la place avant
# de la poser : QGIS ne la dimensionne qu'au dessin.
LEGEND_ROW = 3.4
LEGEND_TITLE = 6.0


def _category_count(layer):
    """Nombre d'entrees que la legende de cette couche affichera."""
    renderer = layer.renderer() if layer is not None else None
    if renderer is None or not hasattr(renderer, "categories"):
        return 1
    return len(renderer.categories()) or 1


def _legend_below_height(count):
    """Hauteur qu'occupera une legende posee sous la carte."""
    lignes = -(-count // LEGEND_COLUMNS)
    return LEGEND_TITLE + lignes * LEGEND_ROW + 4.0


def _map_reserve(context, key):
    """Hauteur a reserver pour la carte d'une section, ou zero s'il n'y en a
    pas : c'est ce que le titre doit demander avec lui."""
    layer = (context or {}).get(key)
    if layer is None or not layer.featureCount():
        return 0.0
    hauteur = SECTION_MAP_HEIGHT + 3.0
    count = _category_count(layer)
    if count > LEGEND_SIDE_MAX:
        hauteur += _legend_below_height(count)
    return hauteur


def _section_map(cursor, context, thematic, legend_title, support=()):
    """Carte du bassin habillee d'une couche thematique, avec sa legende.

    Une section d'occupation du sol ou d'agriculture qui n'aligne que des
    tableaux se lit mal : c'est la carte qui dit ou sont les choses, et le
    tableau qui dit combien. Elles se completent, et la carte doit venir en
    premier - on regarde avant de compter.

    Le fond de plan et le voile exterieur sont ceux de la page 1, deja
    construits : les refaire couterait deux couches de plus a garder en vie
    jusqu'a l'export.
    """
    if thematic is None or not thematic.featureCount():
        return
    if context is None or context.get("basin") is None:
        return

    from qgis.core import QgsLayoutItemMap

    hauteur = SECTION_MAP_HEIGHT
    entrees = _category_count(thematic)
    # Peu d'entrees : la legende tient a droite de la carte. Beaucoup : elle
    # passe dessous, sur deux colonnes, et la carte prend toute la largeur.
    dessous = entrees > LEGEND_SIDE_MAX
    largeur_carte = 186.0 if dessous else SECTION_MAP_WIDTH
    total = hauteur + 3.0
    if dessous:
        total += _legend_below_height(entrees)
    cursor.ensure(total)

    carte = QgsLayoutItemMap(cursor.layout)
    carte.attemptMove(QgsLayoutPoint(MARGIN, cursor.y, MM), True, False,
                      cursor.page)
    carte.attemptResize(QgsLayoutSize(largeur_carte, hauteur, MM))
    carte.setFrameEnabled(True)
    carte.setFrameStrokeColor(GRIS)
    carte.setFrameStrokeWidth(QgsLayoutMeasurement(0.2, MM))
    carte.setBackgroundColor(QColor(255, 255, 255))

    # Les couches d'appui se glissent sous la couche thematique : des points
    # d'obstacles poses sur un fond vide ne diraient rien, c'est le chevelu
    # qui donne son sens a leur position.
    pile = [thematic]
    pile.extend(c for c in support if c is not None)
    pile.append(context["basin"])
    if context.get("mask") is not None:
        pile.append(context["mask"])
    if context.get("basemap") is not None:
        pile.append(context["basemap"])
    carte.setLayers(pile)
    carte.setKeepLayerSet(True)
    cursor.layout.addLayoutItem(carte)

    extent = context["basin"].extent()
    extent.grow(max(extent.width(), extent.height()) * 0.06)
    carte.zoomToExtent(extent)

    if dessous:
        _layer_legend(
            cursor.layout, carte, thematic, context["project"], legend_title,
            MARGIN, cursor.y + hauteur + 2.0, 186.0, page=cursor.page,
            columns=LEGEND_COLUMNS,
        )
        cursor.y += hauteur + 2.0 + _legend_below_height(entrees)
    else:
        _layer_legend(
            cursor.layout, carte, thematic, context["project"], legend_title,
            MARGIN + SECTION_MAP_WIDTH + 4.0, cursor.y,
            SECTION_LEGEND_WIDTH, page=cursor.page,
        )
        cursor.y += hauteur + 3.0


def _layer_legend(layout, map_item, layer, project, title, x, y, width,
                  page=0, title_size=7.0, label_size=6.0, columns=1):
    """Legende d'une seule couche, posee ou on le demande.

    Elle est construite sur l'arbre du modele, vide de ce qu'il portait : la
    legende automatique de QGIS reprendrait tout le projet de l'utilisateur,
    fond de plan et couches de travail comprises.

    L'arbre est celui du modele et non un QgsLayerTree fabrique ici. Un arbre
    cree cote Python et confie au modele lui appartient desormais, mais
    Python en garde la seule reference : le ramasse-miettes le detruit sous
    le modele et QGIS tombe, sans message, au moment de l'apercu.
    """
    if layer is None or not layer.featureCount():
        return None

    from qgis.core import QgsLayoutItem, QgsLayoutItemLegend, QgsLegendStyle

    # La couche doit etre connue du projet pour que le noeud se resolve.
    if project.mapLayer(layer.id()) is None:
        project.addMapLayer(layer, False)

    legend = QgsLayoutItemLegend(layout)
    legend.setLinkedMap(map_item)
    legend.setTitle(title)
    legend.setAutoUpdateModel(False)

    root = legend.model().rootGroup()
    for child in list(root.children()):
        root.removeChildNode(child)
    node = root.addLayer(layer)
    node.setName("")

    legend.setStyleFont(QgsLegendStyle.Style.Title,
                        QFont("Arial", int(title_size), 75))
    legend.setStyleFont(QgsLegendStyle.Style.SymbolLabel,
                        QFont("Arial", int(label_size)))
    legend.setSymbolWidth(3.6)
    legend.setSymbolHeight(2.2)
    legend.rstyle(QgsLegendStyle.Style.Title).setMargin(
        QgsLegendStyle.Side.Bottom, 1.2)
    legend.rstyle(QgsLegendStyle.Style.Symbol).setMargin(
        QgsLegendStyle.Side.Top, 0.4)
    # Les intitules de formation et de culture sont longs : sans repli, la
    # legende s'etale au-dela de la page.
    legend.setWrapString("\n")
    legend.setColumnCount(columns)
    # setColumnCount ne suffit pas : sans setSplitLayer, QGIS garde les
    # entrees d'une meme couche dans une seule colonne. La legende occupe
    # alors deux colonnes de large en restant aussi haute qu'avant, et vient
    # recouvrir les lignes qui la suivent.
    legend.setSplitLayer(columns > 1)
    legend.setEqualColumnWidth(True)
    legend.setResizeToContents(True)

    legend.setBackgroundEnabled(True)
    legend.setBackgroundColor(QColor(255, 255, 255, 220))
    legend.setFrameEnabled(True)
    legend.setFrameStrokeColor(GRIS)
    legend.setFrameStrokeWidth(QgsLayoutMeasurement(0.2, MM))

    layout.addLayoutItem(legend)
    legend.setReferencePoint(QgsLayoutItem.ReferencePoint.UpperLeft)
    legend.attemptMove(QgsLayoutPoint(x, y, MM), True, False, page)
    legend.attemptResize(QgsLayoutSize(width, 10.0, MM))
    return legend


def _zonage_legend(layout, map_item, zonages, project):
    """Legende des zonages, posee dans le coin bas droit de la carte.

    Elle est construite sur un arbre de couches a nous, reduit a la seule
    couche des zonages : la legende automatique de QGIS reprendrait tout le
    projet de l'utilisateur, fond de plan et couches de travail comprises.

    Le nom de la couche est efface du noeud, le titre de l'encadre le disant
    deja ; ne restent que les categories, une ligne par zonage present. Sans
    legende, la carte serait un aplat de couleurs sans clef - jolie et
    inutilisable.
    """
    if zonages is None or not zonages.featureCount():
        return None

    from qgis.core import (
        QgsLayoutItem, QgsLayoutItemLegend, QgsLegendStyle,
    )

    # La couche doit etre connue du projet pour que le noeud se resolve. Elle
    # l'est deja quand le rapport suit un calcul range dans le projet ; elle ne
    # l'est pas depuis Processing, d'ou cette inscription discrete.
    if project.mapLayer(zonages.id()) is None:
        project.addMapLayer(zonages, False)

    legend = QgsLayoutItemLegend(layout)
    legend.setLinkedMap(map_item)
    legend.setTitle("Zonages environnementaux")
    legend.setAutoUpdateModel(False)

    # On vide l'arbre existant du modele plutot que d'en fabriquer un neuf.
    # Un QgsLayerTree cree cote Python et confie au modele lui appartient
    # desormais, mais Python en garde la seule reference : le ramasse-miettes
    # le detruit sous le modele et QGIS tombe. Le defaut est immediat et sans
    # message - la fenetre disparait au moment de l'apercu.
    root = legend.model().rootGroup()
    for child in list(root.children()):
        root.removeChildNode(child)
    node = root.addLayer(zonages)
    node.setName("")

    legend.setStyleFont(QgsLegendStyle.Style.Title, QFont("Arial", 7, 75))
    legend.setStyleFont(QgsLegendStyle.Style.SymbolLabel, QFont("Arial", 6))
    legend.setSymbolWidth(4.0)
    legend.setSymbolHeight(2.4)
    legend.rstyle(QgsLegendStyle.Style.Title).setMargin(
        QgsLegendStyle.Side.Bottom, 1.2)
    legend.rstyle(QgsLegendStyle.Style.Symbol).setMargin(
        QgsLegendStyle.Side.Top, 0.4)

    legend.setBackgroundEnabled(True)
    legend.setBackgroundColor(QColor(255, 255, 255, 220))
    legend.setFrameEnabled(True)
    legend.setFrameStrokeColor(GRIS)
    legend.setFrameStrokeWidth(QgsLayoutMeasurement(0.2, MM))

    layout.addLayoutItem(legend)
    # Ancree par son coin bas droit : l'encadre grandit vers le haut a mesure
    # que les zonages sont nombreux, sans jamais deborder de la carte ni
    # venir sur la barre d'echelle, qui occupe le coin oppose.
    legend.setReferencePoint(QgsLayoutItem.ReferencePoint.LowerRight)
    legend.attemptMove(
        QgsLayoutPoint(A4_WIDTH - MARGIN - 2, 144, MM), True, False, 0)
    return legend


DETAILS_TITLE = "Caractéristiques détaillées du bassin"


def _details_header(layout, page, subtitle, first=True, heading=DETAILS_TITLE):
    """Titre d'une page de detail. Les suivantes portent la mention (suite).

    heading permet a une page de detail differente - les sources, par
    exemple - de reutiliser le meme habillage sous son propre titre.
    """
    _label(layout, heading if first else heading + " (suite)",
           MARGIN, 10, 150, 7, size=13, bold=True, page=page)
    _label(layout, subtitle or "", MARGIN, 18, 186, 5, size=8, color=GRIS,
           page=page)


def _build_details_page(layout, details, title, leftovers=None,
                        values=None, context=None):
    """Ajoute les pages de detail des zonages et de l'eau, s'il y a lieu.

    Il y en a une, ou dix : le contenu decide. Une page vide serait pire que
    pas de page - elle ferait croire a une donnee manquante la ou il n'y a
    rien a dire - mais un contenu tronque serait pire encore, puisque rien
    n'avertirait le lecteur de ce qu'il ne voit pas.

    Renvoie les pages ecrites, sans poser leur pied de page : la page des
    sources vient encore apres, et le compte total qu'un pied de page annonce
    doit attendre qu'elle existe pour etre juste.
    """
    if not _has_details(details) and not leftovers:
        return ()

    from qgis.core import QgsLayoutItemPage

    page_item = QgsLayoutItemPage(layout)
    page_item.setPageSize(QgsLayoutSize(A4_WIDTH, A4_HEIGHT, MM))
    layout.pageCollection().addPage(page_item)
    index = layout.pageCollection().pageCount() - 1
    _details_header(layout, index, title, first=True)

    structures = details.get("structures") or {}

    # Les sections reportees de la page 1 encadrent celles qui sont reprises
    # en detail, chacune de son cote, pour que l'ordre de la fiche soit tenu :
    # ce qui venait avant l'occupation du sol reste devant, ce qui venait
    # apres reste derriere.
    avant, apres = _split_leftovers(leftovers)

    cursor = _Cursor(layout, index, title)
    _fill_leftovers(cursor, avant)
    _fill_land_cover(cursor, (details or {}).get("land_cover"), context)
    _fill_agriculture(cursor, (details or {}).get("agriculture"), context)
    _fill_zonages(cursor, details.get("protected"), context)
    _fill_water(cursor, details)
    _fill_obstacles(cursor, structures.get("roe"), context)
    _fill_steu(cursor, (details or {}).get("steu"),
              (details or {}).get("population"), values, context)
    _fill_prelevements(cursor, (details or {}).get("prelevements"), context)
    _fill_gauges(cursor, structures.get("hydrometrie"))
    _fill_leftovers(cursor, apres)

    return cursor.pages


def _details_footers(layout, pages,
                     note="Détail complet dans le classeur accompagnant "
                          "ce rapport."):
    """Pied de page de chaque page de detail, avec sa pagination.

    La pagination n'apparait que sur ces pages : la premiere ne bouge pas, et
    c'est ici qu'un lecteur a besoin de savoir s'il en manque une - un
    tableau qui s'arrete en bas de feuille ne dit pas, seul, qu'il continue.
    Le compte porte sur le rapport entier, page de garde comprise.
    """
    total = layout.pageCollection().pageCount()
    for page in pages:
        _label(layout, note,
               MARGIN, A4_HEIGHT - 12, 110, 5, size=6.5, color=GRIS,
               page=page)
        _label(layout, "Page {0} sur {1}".format(page + 1, total),
               A4_WIDTH - MARGIN - 76, A4_HEIGHT - 12, 40, 5, size=6.5,
               color=GRIS, align_right=True, page=page)
        _label(layout, "Produit par BVLIP", A4_WIDTH - MARGIN - 32,
               A4_HEIGHT - 12, 32, 5, size=6.5, color=GRIS, align_right=True,
               page=page)


SOURCES_TITLE = "Sources et méthode"

SOURCES_COLUMNS = (
    (0.0, 30.0, False),      # theme
    (31.0, 58.0, False),     # jeu de donnees
    (90.0, 48.0, False),     # fournisseur / service
    (139.0, 47.0, False),    # couche ou reference technique
)

# (theme, jeu de donnees, fournisseur et service, couche ou reference
# technique) - une ligne par jeu de donnees que le pipeline peut interroger,
# qu'il ait ete demande ou non sur ce bassin precis. Un chiffre du rapport
# qui ne remonterait pas jusqu'ici serait un chiffre dont personne ne saurait
# dire d'ou il vient ; la table est donc tenue a la main, a cote de
# core.datasets, plutot que devinee a partir de ce qu'un bassin a rendu.
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
     "naturelles nationale et régionale, parc naturel régional, Ramsar",
     "INPN / Patrinat — Géoplateforme, WFS",
     "patrinat_znieff1, patrinat_znieff2, patrinat_sic, patrinat_zps, "
     "patrinat_apb, patrinat_rnn, patrinat_rnr, patrinat_pnr, "
     "patrinat_ramsar"),
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
    ("Fond de carte", "Plan IGN v2",
     "IGN — Géoplateforme, WMTS", "GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2"),
)


def _build_sources_page(layout, title):
    """Page finale listant l'origine de chaque donnee du rapport.

    A la difference des pages de detail, elle ne depend d'aucun resultat : le
    bassin le plus depouille - un contour sans obstacle ni zonage - a autant
    besoin de savoir d'ou vient son MNT qu'un bassin qui remplit dix pages de
    detail. Elle sort donc toujours, en derniere page.
    """
    from qgis.core import QgsLayoutItemPage

    page_item = QgsLayoutItemPage(layout)
    page_item.setPageSize(QgsLayoutSize(A4_WIDTH, A4_HEIGHT, MM))
    layout.pageCollection().addPage(page_item)
    index = layout.pageCollection().pageCount() - 1
    _details_header(layout, index, title, first=True, heading=SOURCES_TITLE)

    cursor = _Cursor(layout, index, title, heading=SOURCES_TITLE)
    cursor.paragraph(
        "Chaque jeu de données que ce traitement peut interroger, qu'il ait "
        "été demandé ou non sur ce bassin précis. Les services IGN "
        "Géoplateforme et Sandre (eaufrance) sont interrogés sans clé "
        "d'API, en lecture seule.")
    cursor.y += 2.0
    cursor.columns(SOURCES_COLUMNS,
                   ("Thème", "Jeu de données", "Fournisseur / service",
                    "Couche ou référence technique"))
    for theme, dataset, provider, layer_ref in SOURCES:
        cursor.row(SOURCES_COLUMNS, (theme, dataset, provider, layer_ref))
    cursor.y += 1.5
    cursor.paragraph(
        "Les normes de rejet des stations de traitement (STEU) ne sont pas "
        "rapatriées : n'existant nulle part en donnée ouverte station par "
        "station, elles sont calculées à partir de la capacité et de la "
        "zone sensible de chaque station, d'après l'arrêté du 21 juillet "
        "2015 relatif aux systèmes d'assainissement collectif. L'arrêté "
        "préfectoral propre à chaque ouvrage peut être plus strict, jamais "
        "plus permissif.", size=6.5)
    cursor.y += 1.0
    cursor.paragraph(
        "La population du bassin, quand elle figure dans la section STEU, "
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
        "bourg-centre à cheval sur la limite communale.", size=6.5)
    cursor.y += 1.0
    cursor.paragraph(
        "Les prélèvements d'eau ne mesurent que ce qu'Hub'Eau publie : le "
        "service ne filtre pas par emprise géographique, seulement par "
        "commune, si bien que le relevé part des communes qui recoupent le "
        "bassin puis ne garde que les ouvrages dont le point tombe "
        "réellement dedans. Chaque ouvrage porte plusieurs années "
        "déclarées ; seule la plus récente connue est retenue, qui peut "
        "dater de plusieurs années selon l'ouvrage — l'année retenue "
        "figure sur chaque ligne du relevé.", size=6.5)

    _details_footers(
        layout, cursor.pages,
        note="Fond de plan : Plan IGN v2 (Géoplateforme).")


def _split_leftovers(leftovers):
    """Trie les sections reportees autour de celles reprises en detail.

    Celles que les pages de detail redonnent en entier - occupation du sol,
    zonages, masses d'eau - sont ecartees : les reporter en resume juste
    au-dessus de leur propre detail les ecrirait deux fois. Les autres se
    repartissent selon qu'elles precedaient ou suivaient, dans la fiche, la
    premiere section ainsi reprise.
    """
    from ..core.results import DETAILED_SECTIONS

    avant, apres = [], []
    vues = False
    for section, rows in leftovers or ():
        if section in DETAILED_SECTIONS:
            vues = True
            continue
        (apres if vues else avant).append((section, rows))
    return avant, apres


def _fill_leftovers(cursor, leftovers):
    """Sections de la fiche que la page 1 n'a pas pu porter.

    Elles gardent leur titre et leur ordre : le lecteur retrouve la suite de
    ce qu'il lisait, sans avoir a deviner que la page 1 s'etait arretee en
    chemin.
    """
    for section, rows in leftovers or ():
        cursor.section(section)
        for label, value in rows:
            cursor.pair(label, _format(value))


def _fill_land_cover(cursor, cover, context=None):
    """Occupation du sol au complet : Corine, bati, couvert forestier.

    La page 1 n'en montre que les grandes masses, faute de place. Le detail
    des quarante-quatre classes de Corine et des formations de la BD Foret ne
    vivait jusqu'ici que dans le classeur : il fallait donc l'ouvrir pour
    savoir ce que recouvrent les cinquante-quatre pour cent de "forets et
    milieux semi-naturels" annonces en page 1.
    """
    cover = cover or {}
    corine = cover.get("corine") or {}
    bati = cover.get("bati") or {}
    forest = cover.get("foret") or {}
    if not (corine.get("classes") or bati or forest.get("formations")):
        return

    cursor.section("Occupation du sol", _map_reserve(context, "foret"),
                   page_break=True)
    _section_map(cursor, context, (context or {}).get("foret"),
                 "Formations BD Forêt v2")

    classes = corine.get("classes") or []
    if classes:
        cursor.pair("Classe dominante (Corine Land Cover 2018)",
                    "{0} — {1} %".format(classes[0]["libelle"],
                                         _number(classes[0]["part_pct"], 1)))
        if corine.get("couverture_pct") is not None:
            cursor.pair("Couverture atteinte par Corine Land Cover",
                        _number(corine["couverture_pct"], 1) + " %")
        cursor.y += 1.5
        cursor.columns(CLC_COLUMNS,
                       ("Code", "Classe Corine Land Cover 2018",
                        "Surface (ha)", "Part (%)"))
        for item in classes:
            cursor.row(CLC_COLUMNS, (
                item["code"], item["libelle"],
                _number(item["surface_ha"]), _number(item["part_pct"], 1),
            ))

    if bati.get("batiment_nb") is not None:
        cursor.y += 1.5
        cursor.pair("Bâtiments BD TOPO dans le bassin",
                    "{0} bâtiment(s)".format(bati["batiment_nb"]))
        if bati.get("batiment_ha") is not None:
            cursor.pair("Emprise au sol des bâtiments",
                        "{0} ha, soit {1} % du bassin".format(
                            _number(bati["batiment_ha"], 3),
                            _number(bati.get("batiment_pct"), 2)))
        if bati.get("zone_habitation_pct") is not None:
            cursor.pair("Zones d'habitation BD TOPO",
                        _number(bati["zone_habitation_pct"], 2) + " % du "
                        "bassin")

    formations = forest.get("formations") or []
    if formations:
        cursor.y += 2.0
        _land_cover_note(cursor, corine, forest)
        cursor.y += 1.5
        # Les deux totaux sont rappeles ensemble : c'est cote a cote que
        # l'ecart entre couvert et surface boisee se comprend.
        cursor.pair("Couvert BD Forêt v2, landes comprises",
                    "{0} ha, soit {1} % du bassin".format(
                        _number(forest.get("surface_ha")),
                        _number(forest.get("part_pct"), 1)))
        cursor.pair("Surface boisée, peuplements seuls",
                    "{0} ha, soit {1} % du bassin".format(
                        _number(forest.get("boisee_ha")),
                        _number(forest.get("boisee_pct"), 1)))
        cursor.y += 1.5
        cursor.columns(FOREST_COLUMNS,
                       ("Formation végétale (BD Forêt v2)",
                        "Surface (ha)", "Part (%)"))
        for item in formations:
            cursor.row(FOREST_COLUMNS, (
                item["libelle"], _number(item["surface_ha"]),
                _number(item["part_pct"], 1),
            ))


def _land_cover_note(cursor, corine, forest):
    """Pourquoi Corine et la BD Foret ne disent pas la meme chose du boise.

    Les deux chiffres se suivent dans la meme section et different volontiers
    de dix points : sans un mot d'explication, le lecteur conclut qu'une des
    deux sources se trompe, alors qu'elles ne mesurent pas la meme chose. La
    note porte les valeurs du bassin plutot qu'un discours general - c'est
    l'ecart qu'il a sous les yeux qu'il faut lui expliquer.
    """
    naturel = None
    for groupe in corine.get("niveaux1") or ():
        if groupe.get("code") == "3":
            naturel = groupe.get("part_pct")

    chiffres = ""
    if naturel is not None and forest.get("part_pct") is not None:
        chiffres = (
            " Ici : {0} % pour Corine, {1} % de couvert et {2} % de "
            "peuplements pour la BD Forêt.".format(
                _number(naturel, 1), _number(forest["part_pct"], 1),
                _number(forest.get("boisee_pct"), 1))
        )

    cursor.paragraph(
        "Corine couvre tout le territoire mais ignore ce qui fait moins de "
        "25 ha, et range landes, pelouses et roches nues avec les bois ; la "
        "BD Forêt n'inventorie que la forêt, à 0,5 ha près. Les deux ne "
        "s'additionnent pas, et l'écart n'est l'erreur de personne." +
        chiffres
    )


def _fill_agriculture(cursor, agri, context=None):
    """Agriculture declaree a la PAC, avec sa synthese.

    Le rapport porte deux chiffres d'agriculture qui ne coincident pas : la
    part de "territoires agricoles" de Corine et la surface declaree au RPG.
    Comme pour la foret, la note dit pourquoi, avec les valeurs du bassin.
    """
    agri = agri or {}
    rpg = agri.get("rpg") or {}
    prairies = agri.get("prairies") or {}
    aoc = agri.get("aoc") or {}
    if not (rpg.get("nb_parcelles") or prairies.get("nb") or aoc.get("nb")):
        return

    cursor.section("Agriculture déclarée (PAC)",
                   _map_reserve(context, "parcelles"), page_break=True)
    _section_map(cursor, context, (context or {}).get("parcelles"),
                 "Cultures déclarées")

    if rpg.get("nb_parcelles"):
        cursor.pair("Surface déclarée dans le bassin",
                    "{0} ha, soit {1} % du bassin".format(
                        _number(rpg["surface_ha"]),
                        _number(rpg["part_pct"], 1)))
        cursor.pair("Parcelles déclarées",
                    "{0}, de {1} ha en moyenne ({2} ha en médiane)".format(
                        rpg["nb_parcelles"],
                        _number(rpg["taille_moyenne_ha"]),
                        _number(rpg["taille_mediane_ha"])))

        if rpg.get("herbe_ha") is not None:
            # La distinction qui commande la lecture d'un bassin versant :
            # l'herbe retient l'eau et le sol, la culture les laisse partir.
            cursor.y += 1.0
            cursor.columns(AGRI_COLUMNS,
                           ("Prairies et cultures", "Surface (ha)",
                            "Part du bassin (%)"))
            cursor.row(AGRI_COLUMNS, (
                "Prairies et surfaces pastorales",
                _number(rpg["herbe_ha"]), _number(rpg["herbe_pct"], 1),
            ))
            cursor.row(AGRI_COLUMNS, (
                "Cultures", _number(rpg["cultures_ha"]),
                _number(rpg["cultures_pct"], 1),
            ))
            if rpg.get("herbe_part_declare") is not None:
                cursor.note(
                    "Soit {0} % d'herbe et {1} % de cultures dans la surface "
                    "déclarée.".format(
                        _number(rpg["herbe_part_declare"], 1),
                        _number(rpg["cultures_part_declare"], 1)))

        categories = rpg.get("categories") or []
        if categories:
            cursor.y += 1.0
            cursor.columns(AGRI_COLUMNS,
                           ("Catégorie de culture", "Surface (ha)",
                            "Part (%)"))
            for item in categories:
                cursor.row(AGRI_COLUMNS, (
                    item["libelle"], _number(item["surface_ha"]),
                    _number(item["part_pct"], 1),
                ))

        cultures = rpg.get("cultures") or []
        if cultures:
            cursor.y += 1.5
            cursor.columns(CULTURE_COLUMNS,
                           ("Code", "Culture déclarée", "Surface (ha)",
                            "Part (%)"))
            for item in cultures:
                cursor.row(CULTURE_COLUMNS, (
                    item["code"], item["libelle"],
                    _number(item["surface_ha"]), _number(item["part_pct"], 1),
                ))

    bio = agri.get("bio") or {}
    if bio.get("nb_parcelles"):
        cursor.y += 1.5
        cursor.pair("Certifiée agriculture biologique",
                    "{0} ha, soit {1} % du bassin".format(
                        _number(bio["certifie_ha"]),
                        _number(bio["certifie_pct"], 1)))
        if bio.get("conversion_ha"):
            cursor.pair("En conversion vers le biologique",
                        "{0} ha, soit {1} % du bassin".format(
                            _number(bio["conversion_ha"]),
                            _number(bio["conversion_pct"], 1)))
        cursor.pair("Parcelles engagées",
                    "{0}, soit {1} % de la surface déclarée".format(
                        bio["nb_parcelles"],
                        _number(bio.get("part_declare"), 1)))

    if prairies.get("nb"):
        cursor.y += 1.5
        cursor.pair("Prairies sensibles (BCAE, en zone Natura 2000)",
                    "{0} ha, soit {1} % du bassin".format(
                        _number(prairies["surface_ha"]),
                        _number(prairies["part_pct"], 1)))
    if aoc.get("nb"):
        cursor.pair("Aires AOC viticoles (INAO)",
                    "{0} ha, soit {1} % du bassin".format(
                        _number(aoc["surface_ha"]),
                        _number(aoc["part_pct"], 1)))

    if rpg.get("nb_parcelles"):
        cursor.y += 2.0
        cursor.paragraph(
            "Le RPG ne recense que le déclaré : un exploitant qui ne demande "
            "pas d'aide de la PAC n'y figure pas, et la surface ci-dessus "
            "minore donc la surface agricole réelle. Elle ne se compare pas "
            "non plus terme à terme aux « territoires agricoles » de Corine, "
            "qui classe l'usage du sol sans savoir qui déclare quoi. Les deux "
            "répartitions ci-dessus ne se recouvrent pas : l'herbe réunit les "
            "prairies et les surfaces pastorales, quand le RPG range pour sa "
            "part les prairies temporaires avec les terres arables. Les "
            "engagements en mesures agroenvironnementales, eux, ne sont pas "
            "publiés à la parcelle : le bio est ce qui s'en approche le plus "
            "dans les données ouvertes."
        )


def _fill_zonages(cursor, protected, context=None):
    """Un bloc par zonage present, avec ses sites nommes."""
    zonages = [z for z in (protected or {}).get("zonages") or []
               if z.get("nb_sites")]
    if not zonages:
        return

    cursor.section("Zonages environnementaux",
                   _map_reserve(context, "zonages"), page_break=True)
    _section_map(cursor, context, (context or {}).get("zonages"),
                 "Zonages environnementaux")
    cursor.columns(ZONAGE_COLUMNS,
                   ("Zonage", "Site", "Code", "Surface (ha)", "Part (%)"))

    for zonage in zonages:
        for position, site in enumerate(zonage["sites"]):
            # Le nom du zonage n'est rappele que sur sa premiere ligne, mais
            # aussi en tete de page quand ses sites debordent : sans cela,
            # une page qui commence au milieu des ZNIEFF n'en dirait rien.
            entete = position == 0 or cursor.starts_page(ROW)
            cursor.row(ZONAGE_COLUMNS, (
                zonage["libelle"] if entete else "",
                site["nom"],
                site["code"],
                _number(site["surface_ha"]),
                _number(site["part_pct"], 1),
            ))

    # Le total est une union et non une somme : le rappeler ici evite qu'on
    # additionne la colonne de gauche pour verifier.
    cursor.y += 1.0
    cursor.row(ZONAGE_COLUMNS, (
        "Total sans double compte", "", "",
        _number((protected or {}).get("total_ha")),
        _number((protected or {}).get("total_pct"), 1),
    ), bold=True)


def _fill_water(cursor, details):
    """Masse d'eau de surface, nappe et hydroecoregions."""
    body = details.get("water_body") or {}
    meso = details.get("groundwater") or {}
    her = details.get("hydroecoregion") or {}
    if not (body or meso or any(her.values())):
        return

    cursor.section("Masses d'eau et hydroécorégion")
    if body:
        cursor.pair("Masse d'eau DCE de surface — code européen",
                    body.get("code_eu") or "—")
        cursor.pair("Masse d'eau DCE — dénomination du bassin versant",
                    body.get("nom_bv") or "—")
        if body.get("surface_bv_km2") is not None:
            cursor.pair("Masse d'eau DCE — surface de son bassin (km²)",
                        _number(body["surface_bv_km2"]))
        cursor.pair("Exutoire situé dans le bassin de la masse d'eau",
                    _yes_no(body.get("exutoire_dans_le_bv")))
    if meso:
        cursor.pair("Masse d'eau souterraine — code européen",
                    meso.get("code_eu") or "—")
        cursor.pair("Masse d'eau souterraine — dénomination",
                    meso.get("nom") or "—")
        cursor.pair("Masse d'eau souterraine — karstique",
                    _yes_no(meso.get("karstique")))
        if meso.get("surface_affleurante_km2") is not None:
            cursor.pair("Masse d'eau souterraine — affleurement (km²)",
                        _number(meso["surface_affleurante_km2"]))
    if her.get("her1_nom"):
        cursor.pair("Hydroécorégion de niveau 1", "{0} ({1})".format(
            her["her1_nom"], her.get("her1_code") or "—"))
    if her.get("her2_nom"):
        cursor.pair("Hydroécorégion de niveau 2", "{0} ({1})".format(
            her["her2_nom"], her.get("her2_code") or "—"))


def _fill_obstacles(cursor, roe, context=None):
    """Bilan du ROE, puis les ouvrages un a un."""
    if not roe or not roe.get("nb"):
        return

    cursor.section("Obstacles à l'écoulement (ROE)",
                   _map_reserve(context, "obstacles"), page_break=True)
    _section_map(cursor, context, (context or {}).get("obstacles"),
                 "Obstacles à l'écoulement",
                 support=((context or {}).get("reseau"),))
    cursor.pair("Ouvrages recensés dans le bassin", roe["nb"])
    cursor.pair("Dont encore existants", roe.get("nb_existants"))
    cursor.pair("Dont classés Grenelle", roe.get("nb_grenelle"))
    cursor.pair("Dont équipés d'une passe à poissons",
                roe.get("nb_avec_passe"))
    if roe.get("chute_cumulee_m") is not None:
        cursor.pair(
            "Hauteur de chute cumulée, classes comprises (m)",
            "{0} sur {1} ouvrage(s) renseigné(s)".format(
                _number(roe["chute_cumulee_m"]),
                roe.get("nb_chute_connue") or 0))
    if roe.get("chute_max_m") is not None:
        cursor.pair("Plus haute chute (m)", _number(roe["chute_max_m"]))
    if roe.get("par_km") is not None:
        cursor.pair("Densité (ouvrages par km de cours d'eau)",
                    _number(roe["par_km"], 3))

    sites = roe.get("sites") or []
    if not sites:
        return
    cursor.y += 1.5
    cursor.columns(ROE_COLUMNS, ("Code ROE", "Ouvrage", "Type", "Chute (m)",
                                 "Provenance", "Passe à poissons"))
    for site in sites:
        cursor.row(ROE_COLUMNS, (
            site["code"], site["nom"], site["type"],
            _number(site["chute_m"]), site["chute_origine"] or "—",
            _yes_no(site["passe_a_poissons"]),
        ))
    reste = roe["nb"] - len(sites)
    if reste > 0:
        # Ce reste n'existe que si le referentiel a rendu plus d'ouvrages que
        # le plafond de core.obstacles : la page, elle, ne tronque plus rien.
        cursor.note("… et {0} ouvrage(s) au-dela du plafond de relevé."
                    .format(reste))


def _fill_steu(cursor, steu, population=None, values=None, context=None):
    """Bilan des STEU du bassin, la population estimee, puis les stations."""
    if not steu or not steu.get("nb"):
        return

    cursor.section("Stations de traitement des eaux usées (STEU)",
                   _map_reserve(context, "steu"), page_break=True)
    _section_map(cursor, context, (context or {}).get("steu"),
                 "Stations de traitement des eaux usées",
                 support=((context or {}).get("reseau"),))
    cursor.pair("Stations recensées dans le bassin", steu["nb"])
    cursor.pair("Dont en service", steu.get("nb_en_service"))
    if steu.get("capacite_totale_eh") is not None:
        cursor.pair(
            "Capacité nominale cumulée (EH)",
            "{0} sur {1} station(s) renseignée(s)".format(
                _number(steu["capacite_totale_eh"], 0),
                steu.get("nb_capacite_connue") or 0))
    if steu.get("capacite_max_eh") is not None:
        cursor.pair("Plus grosse station (EH)",
                    _number(steu["capacite_max_eh"], 0))
    cursor.pair("Dont ≥ 2 000 EH", steu.get("nb_sup_2000_eh"))
    cursor.pair("Dont rejetant en zone sensible à l'eutrophisation",
                steu.get("nb_zone_sensible"))
    cursor.pair("Dont avec autosurveillance en place",
                steu.get("nb_avec_autosurv"))

    # La population n'est montree qu'ici, comme point de comparaison a la
    # capacite des stations : ce n'est pas un recensement, et la faire
    # figurer au recap general du bassin lui preterait une exactitude
    # qu'elle n'a pas. Voir la methode en derniere page du rapport.
    estimee = (population or {}).get("population_estimee")
    if estimee is not None:
        cursor.y += 1.5
        cursor.pair(
            "Population estimée du bassin",
            "{0} habitant(s), sur {1} commune(s) sur {2} recoupées"
            .format(_number(estimee, 0),
                    population.get("nb_communes_estimees") or 0,
                    population.get("nb_communes") or 0))
        surface_km2 = (values or {}).get("surface_km2")
        if surface_km2:
            cursor.pair("Densité de population estimée (hab./km²)",
                        _number(estimee / surface_km2, 1))
        lin_hydro_km = (values or {}).get("lin_hydro_km")
        if lin_hydro_km:
            cursor.pair(
                "Population estimée par km de cours d'eau (hab./km)",
                _number(estimee / lin_hydro_km, 1))
        if steu.get("capacite_totale_eh"):
            cursor.pair(
                "Capacité STEU cumulée pour cette population (EH/habitant)",
                _number(steu["capacite_totale_eh"] / estimee, 2))
        cursor.note("Estimation, non un recensement — méthode en dernière "
                    "page du rapport.")

    stations = steu.get("stations") or []
    if not stations:
        return
    cursor.y += 1.5
    cursor.columns(STEU_COLUMNS, ("Code Sandre", "Station", "Capacité (EH)",
                                  "Taux de charge (%)", "Commune",
                                  "Autosurveillance"))
    for station in stations:
        cursor.row(STEU_COLUMNS, (
            station["code"], station["nom"] or "—",
            _number(station["capacite_eh"], 0),
            _number(station["taux_charge_pct"], 0),
            station["commune"] or "—",
            station["autosurveillance"] or "non renseigné",
        ))
    reste = steu["nb"] - len(stations)
    if reste > 0:
        # Ce reste n'existe que si le referentiel a rendu plus de stations que
        # le plafond de core.steu.
        cursor.note("… et {0} station(s) au-delà du plafond de relevé."
                    .format(reste))


def _fill_prelevements(cursor, prelevements, context=None):
    """Bilan des prelevements d'eau, par usage, puis les ouvrages un a un."""
    if not prelevements or not prelevements.get("nb"):
        return

    cursor.section("Prélèvements d'eau",
                   _map_reserve(context, "prelevements"), page_break=True)
    _section_map(cursor, context, (context or {}).get("prelevements"),
                 "Prélèvements d'eau",
                 support=((context or {}).get("reseau"),))
    cursor.pair("Ouvrages recensés dans le bassin", prelevements["nb"])
    if prelevements.get("volume_total_m3") is not None:
        cursor.pair("Volume annuel cumulé (m³)",
                    _number(prelevements["volume_total_m3"], 0))
    if prelevements.get("annee_recente") is not None:
        cursor.pair("Année la plus récente connue",
                    prelevements["annee_recente"])

    for usage in prelevements.get("par_usage") or []:
        cursor.pair(usage["usage"], "{0} m³/an".format(
            _number(usage["volume_m3"], 0)))

    ouvrages = prelevements.get("ouvrages") or []
    if not ouvrages:
        return
    cursor.y += 1.5
    cursor.columns(PRELEVEMENT_COLUMNS, ("Ouvrage", "Usage", "Volume (m³/an)",
                                         "Année", "Commune"))
    for ouvrage in ouvrages:
        cursor.row(PRELEVEMENT_COLUMNS, (
            ouvrage["nom"] or ouvrage["code"] or "—",
            ouvrage["usage"] or "non renseigné",
            _number(ouvrage["volume_m3"], 0),
            ouvrage["annee"],
            ouvrage["commune"] or "—",
        ))
    reste = prelevements["nb"] - len(ouvrages)
    if reste > 0:
        # Ce reste n'existe que si le service a rendu plus d'ouvrages que le
        # plafond de core.prelevements.
        cursor.note("… et {0} ouvrage(s) au-delà du plafond de relevé."
                    .format(reste))


def _fill_gauges(cursor, hydro):
    """Stations de jaugeage du bassin."""
    if not hydro:
        return

    cursor.section("Sites hydrométriques")
    if not hydro.get("nb"):
        # Le dire explicitement : un bassin non jauge est une information, et
        # une section absente se lirait comme une donnee non demandee.
        cursor.note("Aucune station de jaugeage dans le bassin.")
        return

    cursor.pair("Stations dans le bassin", hydro["nb"])
    cursor.y += 1.5
    cursor.columns(HYDRO_COLUMNS, ("Code Sandre", "Station", "Gestionnaire"))
    sites = hydro.get("sites") or []
    for site in sites:
        cursor.row(HYDRO_COLUMNS,
                   (site["code"], site["nom"], site["gestionnaire"]))
    reste = hydro["nb"] - len(sites)
    if reste > 0:
        cursor.note("… et {0} station(s) au-delà du plafond de relevé."
                    .format(reste))


def _fill_bottom(layout, values, charts_paths):
    """Deux colonnes : les valeurs a gauche, les graphiques a droite.

    Renvoie les sections que la page n'a pas pu porter, a charge de
    l'appelant de les reporter sur la page de detail.

    Elles etaient auparavant abandonnees sans un mot. La colonne offre cent
    trente et un millimetres et les sections en demandent plus du double : il
    en restait toujours en route, et rien ne le disait. Le defaut est passe
    inapercu tant que la coupure tombait sur les sources de l'exutoire ;
    l'ajout de trois lignes a l'occupation du sol - la surface boisee, les
    feuillus, les coniferes - a fait basculer cette section entiere de
    l'autre cote, avec tout ce qui la suivait. Elle tenait a six dixiemes de
    millimetre pres.
    """
    from ..core.results import ALIASES, REPORT_SECTIONS

    top = 150.0
    column_width = 88.0
    left = MARGIN
    right = MARGIN + column_width + 6

    y = top
    restantes = []
    for section, names in REPORT_SECTIONS:
        rows = [(ALIASES.get(n, n), values.get(n)) for n in names]
        rows = [(label, v) for label, v in rows if v not in (None, "")]
        if not rows:
            continue
        if restantes or y + 5 + 3.6 * len(rows) > A4_HEIGHT - 16:
            # Une section qui ne tient pas renvoie a la page de detail, et
            # celles qui la suivent avec elle : les faire passer devant
            # romprait l'ordre du rapport pour la seule raison qu'elles sont
            # plus courtes.
            restantes.append((section, rows))
            continue
        _label(layout, section, left, y, column_width, 4.5,
               size=8.0, bold=True)
        y += 5.0
        for label, value in rows:
            _label(layout, label, left, y, column_width - 26, 3.4, size=6.4)
            # La valeur est raccourcie a ce que sa colonne peut montrer sur
            # une ligne : la page 1 est un tableau a pas fixe, une valeur qui
            # passerait a la ligne recouvrirait les deux suivantes. Releve
            # sur la Besbre : "LA BESBRE DEPUIS LA RETENUE DE SAINT-CLEMENT
            # JUSQU'A LA CONFLUENCE AVEC LE BARBENAN" tenait sur trois lignes
            # dans vingt-six millimetres, et effacait la surface du bassin
            # versant et la categorie Sandre. Le nom entier figure de toute
            # facon dans la table attributaire et sur la page de detail.
            _label(layout, _ellipsize(_format(value), 26.0),
                   left + column_width - 26, y, 26,
                   3.4, size=6.4, bold=True, align_right=True)
            y += 3.6
        y += 2.0

    chart_y = top
    # Le relief passe en tete : c'est l'image qui se lit d'un coup d'oeil,
    # la ou les courbes demandent qu'on s'y arrete. Ce qui ne tient plus dans
    # la colonne est abandonne par le garde ci-dessous - en pratique le
    # graphique des zonages, dont les parts figurent de toute facon dans le
    # tableau de gauche et le detail dans le classeur.
    for key, height in (("relief", 44), ("hypsometrie", 40),
                        ("occupation", 40), ("zonages", 34)):
        path = (charts_paths or {}).get(key)
        if not path:
            continue
        if chart_y + height > A4_HEIGHT - 16:
            break
        _picture(layout, path, right, chart_y, column_width, height)
        chart_y += height + 3

    return restantes


def _ellipsize(text, width, size=CELL_SIZE, bold=True):
    """Raccourcit un texte jusqu'a ce qu'il tienne sur une ligne.

    Le nombre de caracteres ne suffit pas a en decider : c'est la largeur
    rendue qui compte, et vingt capitales occupent la place de vingt-cinq
    bas-de-casse. On retire donc caractere par caractere jusqu'a ce que la
    mesure passe, en marquant la coupe d'un points de suspension.
    """
    text = str(text)
    if _wrapped_lines(text, width, size=size, bold=bold) <= 1:
        return text
    trimmed = text
    while trimmed and _wrapped_lines(trimmed + "…", width, size=size,
                                     bold=bold) > 1:
        trimmed = trimmed[:-1]
    return (trimmed.rstrip() + "…") if trimmed else text[:1]


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


def print_preview(layout, title, parent=None, dpi=200,
                  export_label=None, on_export=None):
    """Ouvre l'apercu avant impression de la mise en page.

    C'est la meme mise en page que celle du PDF, rendue a l'ecran plutot que
    dans un fichier : ce qu'on voit est donc ce qui sortira, sans avoir rien
    ecrit sur le disque. Le PDF produit, lui, ne peut pas etre affiche tel
    quel - Qt n'embarque de visionneuse PDF que depuis Qt6, et QGIS tourne
    encore en Qt5.

    on_export ajoute un bouton d'export a la barre d'outils de la fenetre, et
    recoit la fenetre en argument pour pouvoir y accrocher son propre
    dialogue. Le geste est celui qu'on attend d'un apercu : on regarde, et si
    la page convient, on l'enregistre sans avoir a refermer et a repartir du
    panneau.

    L'import est fait ici et non en tete de module : QtPrintSupport n'est
    utile qu'a cette fonction, et une installation qui en manquerait ne doit
    pas empecher le rapport de s'exporter.
    """
    from qgis.PyQt.QtGui import QPageLayout, QPageSize
    from qgis.PyQt.QtPrintSupport import QPrinter, QPrintPreviewDialog

    printer = QPrinter()
    printer.setOutputFormat(QPrinter.OutputFormat.NativeFormat)
    # A4 portrait, impose et non herite. Sans cela, la fenetre s'ouvre au
    # format par defaut de l'imprimante du poste - Letter sur une machine
    # configuree en anglais, paysage sur une autre - et l'apercu ne montre
    # plus la page telle qu'elle sortira. La mise en page, elle, est en A4
    # portrait de bout en bout.
    printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    printer.setPageOrientation(QPageLayout.Orientation.Portrait)
    exporter = QgsLayoutExporter(layout)

    def render(target):
        """Appele par la fenetre a chaque fois qu'elle a besoin des pages.

        La mise en page se charge elle-meme du format et des marges de
        l'imprimante : lui imposer les notres ici ferait diverger l'apercu du
        PDF, qui est precisement ce qu'on veut eviter.
        """
        settings = QgsLayoutExporter.PrintExportSettings()
        settings.dpi = dpi
        exporter.print(target, settings)

    dialog = QPrintPreviewDialog(printer, parent)
    dialog.setWindowTitle(title)
    dialog.paintRequested.connect(render)
    if on_export is not None:
        _add_export_button(dialog, export_label or "PDF", on_export)
    _fit_to_screen(dialog, parent)
    return dialog.exec_()


# Taille souhaitee pour l'apercu : une page A4 entiere s'y lit sans zoomer.
# Elle n'est qu'un souhait, borne par l'ecran - voir _fit_to_screen.
PREVIEW_SIZE = (900, 1000)

# Marge laissee autour de la fenetre : la barre des taches en bas, et de quoi
# attraper les bords a la souris.
SCREEN_MARGIN = 80


def _fit_to_screen(dialog, parent=None, wanted=PREVIEW_SIZE):
    """Ouvre la fenetre assez grande pour lire, jamais plus que l'ecran.

    Le defaut etait de poser 900 x 1000 sans rien demander a personne. Sur un
    portable de 1366 x 720, la fenetre depassait de pres de trois cents
    pixels vers le bas : sa barre de defilement et sa navigation de pages
    tombaient hors de l'ecran, et le rapport devenait un document d'une seule
    page - les suivantes existaient sans qu'on puisse les atteindre. Le
    defaut ne se voyait pas sur un grand ecran, ou la fenetre tient.
    """
    from qgis.PyQt.QtGui import QGuiApplication

    screen = None
    if parent is not None and hasattr(parent, "screen"):
        screen = parent.screen()
    if screen is None:
        screen = QGuiApplication.primaryScreen()
    if screen is None:            # pragma: no cover - poste sans ecran
        dialog.resize(*wanted)
        return

    area = screen.availableGeometry()
    width = min(wanted[0], area.width() - SCREEN_MARGIN)
    height = min(wanted[1], area.height() - SCREEN_MARGIN)
    dialog.resize(width, height)
    # Centree sur l'ecran ou elle s'ouvre, et non sur le coin de la fenetre
    # parente : une fenetre bornee par l'ecran doit aussi y tenir en entier.
    dialog.move(area.x() + (area.width() - width) // 2,
                area.y() + (area.height() - height) // 2)


def _add_export_button(dialog, label, on_export):
    """Ajoute l'export a la barre d'outils de l'apercu.

    Qt ne prevoit pas d'enrichir QPrintPreviewDialog : sa barre d'outils est
    montee dans son constructeur et n'est pas exposee. On la retrouve donc
    parmi ses enfants, ce qui est sans risque - au pire elle n'y est pas, et
    le bouton se pose alors sous l'apercu plutot que dans la barre. Reecrire
    la fenetre entiere autour de QPrintPreviewWidget pour placer un bouton
    couterait bien plus que ce garde.
    """
    from qgis.PyQt.QtWidgets import QPushButton, QToolBar

    def run():
        on_export(dialog)

    bar = dialog.findChild(QToolBar)
    if bar is not None:
        bar.addSeparator()
        action = bar.addAction(label)
        action.triggered.connect(run)
        return
    button = QPushButton(label, dialog)
    button.clicked.connect(run)
    layout = dialog.layout()
    if layout is not None:
        layout.addWidget(button)


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
