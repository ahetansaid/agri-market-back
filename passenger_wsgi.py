"""Point d'entrée Passenger (cPanel « Setup Python App ») — backend Django.

Passenger utilise la variable `application` de ce fichier (placé à la racine
de l'app, à côté de manage.py). Chemins auto-détectés → portable quel que soit
le compte / dossier cPanel. WhiteNoise sert /static et /media (Passenger ne les
sert pas), et on reconstruit PATH_INFO (quirk Passenger/cPanel).
"""

import os
import sys
from urllib.parse import unquote

APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "idamarketplace.settings.n0c")

from django.core.wsgi import get_wsgi_application  # noqa: E402
from whitenoise import WhiteNoise  # noqa: E402

_application = get_wsgi_application()
_application = WhiteNoise(
    _application,
    root=os.path.join(APP_DIR, "staticfiles"),
    prefix="/static/",
)
_application.add_files(os.path.join(APP_DIR, "media"), prefix="/media/")


class PassengerPathInfoFix:
    """Passenger ne fournit pas PATH_INFO — on le reconstruit depuis REQUEST_URI."""

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        request_uri = unquote(environ.get("REQUEST_URI", ""))
        script_name = unquote(environ.get("SCRIPT_NAME", ""))
        offset = len(script_name) if request_uri.startswith(script_name) else 0
        environ["PATH_INFO"] = request_uri[offset:].split("?", 1)[0]
        return self.app(environ, start_response)


application = PassengerPathInfoFix(_application)
