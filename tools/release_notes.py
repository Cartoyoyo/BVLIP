# -*- coding: utf-8 -*-
"""Extrait de CHANGELOG.md les notes d'une version, pour sa release GitHub.

    python tools/release_notes.py 1.3.3                -> notes sur la sortie
    python tools/release_notes.py 1.3.3 --out notes.md -> notes dans un fichier

La section va de la ligne « ## [X.Y.Z] » (titre compris, il porte la date)
jusqu'a la section suivante. Version absente du CHANGELOG : sortie vide, le
workflow se rabat alors sur les notes generees par GitHub.
"""

import argparse
import os
import sys

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def extract(version, path=None):
    path = path or os.path.join(PLUGIN_DIR, "CHANGELOG.md")
    with open(path, encoding="utf-8") as handle:
        lines = handle.read().splitlines()
    head = "## [{0}]".format(version)
    section = []
    for line in lines:
        if line.startswith("## ["):
            if section:
                break
            if line.startswith(head):
                section.append(line)
        elif section:
            section.append(line)
    return "\n".join(section).strip() + "\n" if section else ""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="numero sans le v, ex. 1.3.3")
    parser.add_argument("--out", help="fichier de sortie (UTF-8 sans BOM)")
    arguments = parser.parse_args()
    notes = extract(arguments.version)
    if arguments.out:
        with open(arguments.out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(notes)
    else:
        sys.stdout.buffer.write(notes.encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
