# -*- coding: utf-8 -*-
"""Fabrique le ZIP a deposer sur plugins.qgis.org.

    python tools/build_zip.py            -> BVLIP-<version>.zip a cote du dossier
    python tools/build_zip.py --out DOSSIER

Le ZIP contient un unique dossier racine nomme comme le paquet Python, faute
de quoi QGIS refuse l'installation. Tout ce qui ne sert pas a l'execution en
est exclu : outils de developpement, caches, journaux de version.

Le perimetre defini ici doit rester le meme que celui passe en --exclude au
controle de prepublication, sans quoi on corrige des fichiers qui ne partent
pas, ou on en oublie qui partent.
"""

import argparse
import os
import sys
import zipfile

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGE = "BVLIP"

# Dossiers entierement exclus.
EXCLUDED_DIRS = {"tools", "screenshot", "__pycache__", ".git",
                 ".vscode"}

# Fichiers exclus par extension ou par nom.
EXCLUDED_SUFFIXES = (".pyc", ".pyo", ".bak", ".zip", ".log")
EXCLUDED_NAMES = {".gitignore", "CHANGELOG.md"}

# Les captures d'ecran servent au README du depot, que GitHub rend depuis le
# depot lui-meme : les embarquer dans le ZIP le ferait passer de 0,13 a
# pres d'un megaoctet sans rien apporter a l'execution.


def read_version():
    path = os.path.join(PLUGIN_DIR, "metadata.txt")
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("version="):
                return line.split("=", 1)[1].strip()
    raise SystemExit("Version absente de metadata.txt")


def wanted(root, name):
    if name in EXCLUDED_NAMES:
        return False
    if name.endswith(EXCLUDED_SUFFIXES):
        return False
    parts = set(os.path.relpath(root, PLUGIN_DIR).split(os.sep))
    return not (parts & EXCLUDED_DIRS)


def build(destination):
    version = read_version()
    target = os.path.join(destination, "{0}-{1}.zip".format(PACKAGE, version))
    count = 0
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for root, dirs, files in os.walk(PLUGIN_DIR):
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            for name in sorted(files):
                if not wanted(root, name):
                    continue
                full = os.path.join(root, name)
                relative = os.path.relpath(full, PLUGIN_DIR)
                archive.write(full, os.path.join(PACKAGE, relative))
                count += 1
    size = os.path.getsize(target) / 1e6
    print("{0}\n  {1} fichiers, {2:.2f} Mo".format(target, count, size))
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=os.path.dirname(PLUGIN_DIR),
                        help="dossier de destination du ZIP")
    arguments = parser.parse_args()
    build(arguments.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
