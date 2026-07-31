"""Point d'entrée Passenger/LiteSpeed (cPanel n0c) — backend Django.

L'hébergeur cherche la variable `application` de ce fichier (à la racine de
l'app). On FORCE le module de settings n0c : sur LiteSpeed, DJANGO_SETTINGS_MODULE
peut être pré-défini sur `production` (config DB en SSL incompatible avec le
Postgres local cPanel) → 500. WhiteNoise sert /static et /media, et on
reconstruit PATH_INFO (quirk Passenger/LiteSpeed).
"""

import os
import sys
from urllib.parse import unquote

APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

# NE PAS utiliser setdefault ici : il faut ÉCRASER une éventuelle valeur
# pré-définie par l'hôte (ex. production) pour garantir la config n0c.
os.environ["DJANGO_SETTINGS_MODULE"] = "idamarketplace.settings.n0c"

from django.core.wsgi import get_wsgi_application  # noqa: E402
from whitenoise import WhiteNoise  # noqa: E402

_application = get_wsgi_application()
_application = WhiteNoise(
    _application,
    root=os.path.join(APP_DIR, "staticfiles"),
    prefix="/static/",
)
# add_files seulement si le dossier existe (évite un plantage si media vide).
if os.path.isdir(os.path.join(APP_DIR, "media")):
    _application.add_files(os.path.join(APP_DIR, "media"), prefix="/media/")


class PassengerPathInfoFix:
    """Reconstruit PATH_INFO depuis REQUEST_URI (non fourni par Passenger)."""

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        uri = unquote(environ.get("REQUEST_URI", ""))
        sn = unquote(environ.get("SCRIPT_NAME", ""))
        off = len(sn) if uri.startswith(sn) else 0
        environ["PATH_INFO"] = uri[off:].split("?", 1)[0]
        return self.app(environ, start_response)


application = PassengerPathInfoFix(_application)
