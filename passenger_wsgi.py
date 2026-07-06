import os
import sys

from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

# Set up paths and environment variables

sys.path.append("/home/kpfdvptmns/var/www/idainternational")
os.environ["DJANGO_SETTINGS_MODULE"] = "idamarketplace.settings.production"

# Set script name
SCRIPT_NAME = os.getcwd()


class PassengerPathInfoFix(object):
    """
    Sets PATH_INFO from REQUEST_URI because Passenger doesn't provide it.
    """

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        from urllib.parse import unquote

        environ["SCRIPT_NAME"] = SCRIPT_NAME
        request_uri = unquote(environ["REQUEST_URI"])
        script_name = unquote(environ.get("SCRIPT_NAME", ""))
        offset = len(script_name) if request_uri.startswith(script_name) else 0
        environ["PATH_INFO"] = request_uri[offset:].split("?", 1)[0]
        return self.app(environ, start_response)


# Set the application
# Remplacez la fin du fichier par :
application = get_wsgi_application()
application = WhiteNoise(
    application,
    root="/home/kpfdvptmns/var/www/idainternational/staticfiles",
    prefix="/static/",  # Ajout crucial
)
application.add_files(
    "/home/kpfdvptmns/var/www/idainternational/media", prefix="/media/"
)
application = PassengerPathInfoFix(application)  # Gardez cette ligne en dernier
