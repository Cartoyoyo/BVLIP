# -*- coding: utf-8 -*-
"""Controle de la table des champs, avant publication.

    python tools/check_fields.py

Verifie quatre choses :

  - chaque champ porte un intitule, et **l'unite annoncee dans l'intitule
    correspond au suffixe du nom** : un champ nomme en _km2 doit dire des
    kilometres carres, un champ en _pct des pourcentages. C'est le genre
    d'incoherence qui passe inapercue a la relecture et qui fausse un
    rapport ;
  - les noms sont uniques ;
  - **les dix premiers caracteres sont uniques aussi**. Le format Shapefile
    limite les noms de colonnes a dix caracteres : a l'export, deux champs
    dont les dix premiers caracteres coincident se retrouvent renommes
    d'office par OGR, et l'un des deux devient indechiffrable. Le GeoPackage
    n'a pas cette limite, mais rien n'empeche l'utilisateur d'exporter en
    Shapefile, et il ne doit pas y perdre ses colonnes ;
  - les champs texte tiennent dans les 254 caracteres du format DBF ;
  - **les intitules tiennent sur une ligne du rapport A4**. La colonne des
    libelles y fait 62 mm a 6,4 points, soit environ 55 caracteres : au-dela,
    le texte passe a la ligne et recouvre l'intitule suivant. Le defaut ne se
    voit qu'a la relecture du PDF produit.

Sortie 0 si tout va bien, 1 sinon.
"""

import ast
import os
import sys

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHAPEFILE_NAME_LIMIT = 10
DBF_TEXT_LIMIT = 254
REPORT_LABEL_LIMIT = 55


def read_tables():
    """Extrait les tables de champs sans importer QGIS.

    Le module results depend de qgis.core, indisponible hors de son
    environnement : on lit donc l'arbre syntaxique plutot que le module.
    """
    path = os.path.join(PLUGIN_DIR, "core", "results.py")
    with open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read())

    tables = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        if not target.id.endswith("_FIELDS"):
            continue
        if not isinstance(node.value, (ast.List, ast.Tuple)):
            continue          # CLC_LEVEL1_FIELDS est un dictionnaire
        entries = []
        for element in node.value.elts:
            values = []
            for item in element.elts:
                if isinstance(item, ast.Constant):
                    values.append(item.value)
                else:
                    values.append(None)   # le type, non evaluable ici
            entries.append(values)
        tables[target.id] = entries
    return tables


# Suffixes de nom qui annoncent une grandeur mesuree : leur intitule doit
# porter une unite entre parentheses.
MEASURED_SUFFIXES = ("_m", "_km", "_km2", "_ha", "_pct", "_deg", "_h")

# Correspondances sures, ou le suffixe impose un mot precis dans l'intitule.
# Volontairement limitees : _m et _km sont ambigus, un indice de pente global
# se nomme en _km et s'exprime pourtant en m/km, une altitude se nomme en _m
# et s'exprime en m NGF. Mieux vaut ne verifier que ce qui est certain plutot
# que de signaler a tort des intitules justes.
STRICT_UNITS = (
    ("_km2", "km²"),
    ("_ha", "(ha)"),
    ("_pct", "%"),
    ("_deg", "degrés"),
    ("_h", "heures"),
)


def _unit_problem(field, label):
    """Incoherence entre le suffixe du nom et l'unite de l'intitule, ou None."""
    for suffix, token in STRICT_UNITS:
        if field.endswith(suffix) and token not in label:
            return "le nom annonce {0!r}, absent de l'intitule".format(token)
    if field.endswith(MEASURED_SUFFIXES) and "(" not in label:
        return "grandeur mesuree sans unite entre parentheses"
    return None


def check(name, entries):
    problems = []
    seen = {}
    prefixes = {}
    for entry in entries:
        field = entry[0]
        length = entry[2]
        label = entry[5] if len(entry) > 5 else None

        if not label:
            problems.append("  {0} : pas d'intitule".format(field))
        else:
            trouble = _unit_problem(field, label)
            if trouble:
                problems.append(
                    "  {0} : {1} ({2!r})".format(field, trouble, label)
                )

        if field in seen:
            problems.append("  {0} : nom en double".format(field))
        seen[field] = True

        prefix = field[:SHAPEFILE_NAME_LIMIT]
        if prefix in prefixes:
            problems.append(
                "  {0} et {1} : memes {2} premiers caracteres, l'export "
                "Shapefile en renommerait un".format(
                    prefixes[prefix], field, SHAPEFILE_NAME_LIMIT)
            )
        prefixes[prefix] = field

        if label and len(label) > REPORT_LABEL_LIMIT:
            problems.append(
                "  {0} : intitule de {1} caracteres, au-dela des {2} que "
                "tient une ligne du rapport A4".format(
                    field, len(label), REPORT_LABEL_LIMIT)
            )

        if isinstance(length, int) and length > DBF_TEXT_LIMIT:
            problems.append(
                "  {0} : longueur {1}, au-dela des {2} caracteres du "
                "format DBF".format(field, length, DBF_TEXT_LIMIT)
            )
    return problems


def read_list(module, name, column=0):
    """Colonne d'une table declaree en tete d'un module, sans l'importer."""
    path = os.path.join(PLUGIN_DIR, *module.split("/"))
    with open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and target.id == name:
            return [element.elts[column].value for element in node.value.elts]
    return []


def check_zonage_keys():
    """Le catalogue et la table des zonages doivent nommer les memes couches.

    Elles vivent dans deux modules - core/datasets pour ce qui se coche,
    core/protected pour ce qui s'interroge - et rien dans le code ne les
    relie : une cle ajoutee d'un cote et oubliee de l'autre donnerait une
    case qui ne rapatrie rien, ou une couche qu'aucune case ne commande.
    Le defaut ne se verrait qu'a l'usage, sur un rapport incomplet.
    """
    catalogue = [key for key, tab, _on
                 in zip(read_list("core/datasets.py", "DATASETS", 0),
                        read_list("core/datasets.py", "DATASETS", 1),
                        read_list("core/datasets.py", "DATASETS", 2))
                 if tab == "zonages"]
    declared = read_list("core/protected.py", "ZONAGES", 0)
    problems = []
    for key in sorted(set(catalogue) - set(declared)):
        problems.append(
            "  {0} : proposee au catalogue, absente de protected.ZONAGES"
            .format(key))
    for key in sorted(set(declared) - set(catalogue)):
        problems.append(
            "  {0} : interrogee par protected, absente du catalogue"
            .format(key))
    if catalogue != declared and not problems:
        problems.append(
            "  l'ordre des zonages differe entre le catalogue et protected")
    return problems, len(declared)


def read_strings(module, name):
    """Suite de chaines declarees en tete d'un module."""
    path = os.path.join(PLUGIN_DIR, *module.split("/"))
    with open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and target.id == name:
            return [e.value for e in node.value.elts
                    if isinstance(e, ast.Constant)]
    return []


def check_detailed_sections():
    """DETAILED_SECTIONS doit nommer des sections qui existent vraiment.

    La mise en page s'en sert pour ne pas ecrire deux fois une section : une
    fois en resume reporte de la page 1, une fois en detail. Un titre mal
    recopie ne leve aucune erreur - il ne correspond simplement a rien, et la
    section reapparait en double sans que personne ne s'en avise.
    """
    path = os.path.join(PLUGIN_DIR, "core", "results.py")
    with open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    titres = []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and target.id == "REPORT_SECTIONS":
            titres = [e.elts[0].value for e in node.value.elts]
    detaillees = read_strings("core/results.py", "DETAILED_SECTIONS")
    manquants = [t for t in detaillees if t not in titres]
    return ["  {0!r} : reprise en detail, absente de REPORT_SECTIONS".format(t)
            for t in manquants], len(detaillees)


def read_rows(module, name):
    """Table de tuples de constantes declaree en tete d'un module."""
    path = os.path.join(PLUGIN_DIR, *module.split("/"))
    with open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and target.id == name:
            return [
                tuple(item.value if isinstance(item, ast.Constant) else None
                     for item in element.elts)
                for element in node.value.elts
            ]
    return []


def check_sources():
    """La table des sources doit dire la meme chose dans le PDF et le classeur.

    Elle vit en double parce que excel doit rester importable sans QGIS, ce
    qui interdit d'importer layout pour la lui emprunter. Rien d'autre ne
    relie les deux copies : l'une mise a jour sans l'autre se verrait sur un
    document mais pas sur le second, et personne ne le remarquerait avant
    qu'un lecteur compare les deux.
    """
    pdf = read_rows("report/layout.py", "SOURCES")
    classeur = read_rows("report/excel.py", "SOURCES")
    if pdf == classeur:
        return [], len(pdf)
    problems = []
    if len(pdf) != len(classeur):
        problems.append(
            "  {0} ligne(s) dans layout.SOURCES, {1} dans excel.SOURCES"
            .format(len(pdf), len(classeur)))
    for index, (a, b) in enumerate(zip(pdf, classeur)):
        if a != b:
            problems.append(
                "  ligne {0} : {1!r} (PDF) != {2!r} (classeur)"
                .format(index, a, b))
    return problems, max(len(pdf), len(classeur))


def main():
    tables = read_tables()
    if not tables:
        print("Aucune table de champs trouvee.")
        return 1

    failed = False
    for name, entries in sorted(tables.items()):
        problems = check(name, entries)
        if problems:
            failed = True
            print("{0} : {1} probleme(s)".format(name, len(problems)))
            print("\n".join(problems))
        else:
            longs = sum(1 for e in entries
                        if len(e[0]) > SHAPEFILE_NAME_LIMIT)
            print(
                "{0} : {1} champs, tous intitules, prefixes uniques "
                "({2} seront tronques a l'export Shapefile, sans "
                "collision).".format(name, len(entries), longs)
            )

    problems, total = check_detailed_sections()
    if problems:
        failed = True
        print("Sections detaillees : {0} probleme(s)".format(len(problems)))
        print("\n".join(problems))
    else:
        print("Sections detaillees : {0} titres, tous presents dans "
              "REPORT_SECTIONS.".format(total))

    problems, total = check_zonage_keys()
    if problems:
        failed = True
        print("Zonages : {0} probleme(s)".format(len(problems)))
        print("\n".join(problems))
    else:
        print("Zonages : {0} cles, catalogue et protected d'accord."
              .format(total))

    problems, total = check_sources()
    if problems:
        failed = True
        print("Sources : {0} probleme(s)".format(len(problems)))
        print("\n".join(problems))
    else:
        print("Sources : {0} ligne(s), PDF et classeur d'accord."
              .format(total))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
