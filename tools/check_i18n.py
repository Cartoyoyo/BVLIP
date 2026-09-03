# -*- coding: utf-8 -*-
"""Controle des traductions : toute cle doit exister dans les cinq langues,
et toute cle du dictionnaire doit etre reellement utilisee dans le code.

    python tools/check_i18n.py

Sortie 0 si tout est coherent, 1 sinon. A lancer avant chaque publication.
"""

import importlib.util
import os
import re
import sys

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_i18n():
    """Charge i18n/__init__.py isolement, sans passer par le paquet du plugin
    (qui importerait QGIS, indisponible hors de son environnement)."""
    path = os.path.join(PLUGIN_DIR, "i18n", "__init__.py")
    spec = importlib.util.spec_from_file_location("bvlip_i18n", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def used_keys():
    """Cles reellement passees a tr() dans les sources du plugin."""
    pattern = re.compile(r"""tr\(\s*["']([a-z0-9_]+)["']""")
    found = set()
    for root, dirs, files in os.walk(PLUGIN_DIR):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", "tools")]
        for name in files:
            if not name.endswith(".py"):
                continue
            with open(os.path.join(root, name), encoding="utf-8") as handle:
                found.update(pattern.findall(handle.read()))
    return found


def main():
    i18n = load_i18n()
    codes = [code for code, _ in i18n.LANGUAGES]
    problems = []

    for key, entry in sorted(i18n.TR.items()):
        missing = [code for code in codes if not entry.get(code)]
        if missing:
            problems.append(
                "  {0} : langue(s) manquante(s) {1}".format(key, ", ".join(missing))
            )

    declared = set(i18n.TR)
    used = used_keys()
    for key in sorted(used - declared):
        problems.append("  {0} : utilisee dans le code, absente de TR".format(key))
    for key in sorted(declared - used):
        problems.append("  {0} : declaree dans TR, jamais utilisee".format(key))

    if problems:
        print("Incoherences i18n :")
        print("\n".join(problems))
        return 1

    print(
        "i18n OK : {0} cles x {1} langues, toutes utilisees.".format(
            len(declared), len(codes)
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
