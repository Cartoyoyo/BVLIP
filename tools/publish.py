# -*- coding: utf-8 -*-
"""Depose l'archive du plugin sur plugins.qgis.org.

    python tools/publish.py                    # construit le ZIP puis l'envoie
    python tools/publish.py --zip chemin.zip   # envoie une archive existante
    python tools/publish.py --dry-run          # verifie tout, sans envoyer

Le mot de passe n'est jamais passe en argument : il serait visible dans
l'historique du shell et dans la liste des processus. Il est lu dans la
variable d'environnement OSGEO_PASSWORD si elle existe, sinon demande au
clavier sans echo.

    set OSGEO_USER=Cartoyoyo          (Windows)
    export OSGEO_USER=Cartoyoyo       (Linux, macOS)

Une premiere soumission passe en attente de validation par un moderateur ;
une mise a jour est disponible aussitot dans le gestionnaire d'extensions.

Rappel : une version refusee par les controles du depot ne peut pas etre
renvoyee sous le meme numero. Lancer le controle de prepublication avant.
"""

import argparse
import getpass
import os
import sys
import xmlrpc.client

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENDPOINT = "https://{0}:{1}@plugins.qgis.org/plugins/RPC2/"


def read_version():
    path = os.path.join(PLUGIN_DIR, "metadata.txt")
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("version="):
                return line.split("=", 1)[1].strip()
    raise SystemExit("Version absente de metadata.txt")


def credentials():
    user = os.environ.get("OSGEO_USER")
    if not user:
        user = input("Identifiant OSGeo : ").strip()
    password = os.environ.get("OSGEO_PASSWORD")
    if not password:
        password = getpass.getpass("Mot de passe OSGeo (saisie masquee) : ")
    if not user or not password:
        raise SystemExit("Identifiants incomplets.")
    return user, password


def upload(zip_path, user, password):
    with open(zip_path, "rb") as handle:
        payload = handle.read()
    server = xmlrpc.client.ServerProxy(ENDPOINT.format(user, password))
    return server.plugin.upload(xmlrpc.client.Binary(payload))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", help="archive a envoyer ; construite si omise")
    parser.add_argument("--dry-run", action="store_true",
                        help="tout verifier sans rien envoyer")
    arguments = parser.parse_args()

    version = read_version()
    zip_path = arguments.zip
    if not zip_path:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import build_zip
        zip_path = build_zip.build(os.path.dirname(PLUGIN_DIR))

    if not os.path.exists(zip_path):
        raise SystemExit("Archive introuvable : {0}".format(zip_path))
    print("Plugin  : BVLIP {0}".format(version))
    print("Archive : {0} ({1:.0f} Ko)".format(
        zip_path, os.path.getsize(zip_path) / 1024))

    if arguments.dry_run:
        print("Essai a blanc : rien n'a ete envoye.")
        return 0

    user, password = credentials()
    print("Envoi sur plugins.qgis.org en tant que {0}...".format(user))
    try:
        result = upload(zip_path, user, password)
    except xmlrpc.client.ProtocolError as error:
        # 401 : identifiants refuses. 403 : compte sans droit sur ce plugin.
        raise SystemExit(
            "Envoi refuse ({0} {1}). Verifiez vos identifiants sur "
            "https://plugins.qgis.org".format(error.errcode, error.errmsg)
        )
    except xmlrpc.client.Fault as error:
        raise SystemExit("Le depot a refuse l'archive : {0}".format(
            error.faultString))
    print("Envoi accepte : {0}".format(result))
    print("Premiere soumission : le plugin attend la validation d'un "
          "moderateur.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
