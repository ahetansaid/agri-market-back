import os
from pathlib import Path

from .base import *  # noqa: F401, F403, F405

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = os.getenv(
    "ALLOWED_HOSTS",
    "nourdignagrimarket.com,www.nourdignagrimarket.com",
).split(",")

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
        # Neon (et la plupart des Postgres managés) exigent le SSL.
        # DB_SSLMODE=disable pour un Postgres local sans SSL.
        "OPTIONS": {"sslmode": os.getenv("DB_SSLMODE", "require")},
    }
}

for _required in ("DB_NAME", "DB_USER", "DB_PASSWORD"):
    if not os.getenv(_required):
        raise RuntimeError(
            f"{_required} is missing in production. Set it via environment "
            "variables (or .env on the server)."
        )


CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

CORS_ALLOW_CREDENTIALS = True
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SAMESITE = "Lax"

# ---------------------------------------------------------------------------
# Origines autorisées (frontend Vercel), pilotées par variables d'env.
# CORS_EXTRA_ORIGINS  : ex. "https://mon-projet.vercel.app"
# CSRF_TRUSTED_ORIGINS: ex. "https://mon-projet.vercel.app,https://xxx.onrender.com"
# (valeurs multiples séparées par des virgules)
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = CORS_ALLOWED_ORIGINS + [
    o.strip() for o in os.getenv("CORS_EXTRA_ORIGINS", "").split(",") if o.strip()
]
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
]
