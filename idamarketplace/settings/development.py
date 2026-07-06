import os
from pathlib import Path

from .base import *  # noqa: F401, F403, F405

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEBUG = True
ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT"),
    }
}

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": BASE_DIR / "dbmarkeplace.sqlite3",
#         "TEST": {
#             "NAME": "memory:",
#         },
#     }
# }


STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SAMESITE = "Lax"

# DEV : desactive django-axes pour ne pas se bloquer apres 5 tentatives
# ratees pendant les tests. NE PAS desactiver en prod.
AXES_ENABLED = False

# DEV : empeche two_factor de monkey-patcher AdminSite.login (qui redirige
# /admin/login/ vers /accounts/login/). On veut le login admin natif Django
# pour pouvoir tester avec notre template override templates/admin/login.html.
# En prod, ce flag reste True (default) + AdminSiteOTPRequired est applique.
TWO_FACTOR_PATCH_ADMIN = False
