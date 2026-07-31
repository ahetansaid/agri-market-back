"""Réglages de production pour l'hébergement cPanel n0c.

Différences clés vs Render :
  - la base peut être PostgreSQL OU MySQL (cPanel fournit toujours MySQL) →
    les OPTIONS s'adaptent au moteur (sslmode = Postgres uniquement) ;
  - HTTPS est géré par Apache devant Passenger → SECURE_SSL_REDIRECT est
    désactivable par variable d'env pour éviter les boucles de redirection ;
  - disque persistant → les médias uploadés ne disparaissent pas.

À activer via : DJANGO_SETTINGS_MODULE=idamarketplace.settings.n0c
"""

import os
from pathlib import Path

from .base import *  # noqa: F401, F403, F405

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DEBUG = os.getenv("DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv(
        "ALLOWED_HOSTS", "nourdignagrimarket.com,www.nourdignagrimarket.com"
    ).split(",")
    if h.strip()
]

# ---------------------------------------------------------------------------
# Base de données — s'adapte au moteur (PostgreSQL ou MySQL).
#   PostgreSQL : DB_ENGINE=django.db.backends.postgresql  (port 5432)
#   MySQL      : DB_ENGINE=django.db.backends.mysql       (port 3306)
# Sur cPanel, DB_HOST est généralement "localhost".
# ---------------------------------------------------------------------------
_engine = os.getenv("DB_ENGINE", "django.db.backends.postgresql")
_db = {
    "ENGINE": _engine,
    "NAME": os.getenv("DB_NAME"),
    "USER": os.getenv("DB_USER"),
    "PASSWORD": os.getenv("DB_PASSWORD"),
    "HOST": os.getenv("DB_HOST", "localhost"),
    "PORT": os.getenv("DB_PORT", ""),
}
if "postgresql" in _engine:
    _db["PORT"] = _db["PORT"] or "5432"
    # sslmode=disable pour un Postgres local cPanel (sinon "require").
    _db["OPTIONS"] = {"sslmode": os.getenv("DB_SSLMODE", "disable")}
elif "mysql" in _engine:
    _db["PORT"] = _db["PORT"] or "3306"
    _db["OPTIONS"] = {
        "charset": "utf8mb4",
        # Évite les avertissements de troncature silencieuse sur MySQL.
        "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
    }
DATABASES = {"default": _db}

for _required in ("DB_NAME", "DB_USER", "DB_PASSWORD"):
    if not os.getenv(_required):
        raise RuntimeError(
            f"{_required} is missing. Set it in the .env / cPanel env of the app."
        )

# ---------------------------------------------------------------------------
# Sécurité HTTPS (Apache termine le TLS devant Passenger).
# SECURE_SSL_REDIRECT est OFF par défaut : ne l'active (=true) qu'une fois sûr
# que Apache transmet bien X-Forwarded-Proto, sinon risque de boucle 301.
# ---------------------------------------------------------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "False").lower() == "true"
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SAMESITE = "Lax"
CORS_ALLOW_CREDENTIALS = True

# Origines du frontend (même domaine ou sous-domaine), pilotées par env.
CORS_ALLOWED_ORIGINS = CORS_ALLOWED_ORIGINS + [  # noqa: F405
    o.strip() for o in os.getenv("CORS_EXTRA_ORIGINS", "").split(",") if o.strip()
]
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
]

# ---------------------------------------------------------------------------
# Fichiers statiques & médias — servis par Apache depuis le disque cPanel.
# WhiteNoise reste en secours. MEDIA_ROOT persiste (contrairement à Render).
# ---------------------------------------------------------------------------
STATIC_ROOT = os.getenv("STATIC_ROOT", os.path.join(BASE_DIR, "staticfiles"))
MEDIA_ROOT = os.getenv("MEDIA_ROOT", os.path.join(BASE_DIR, "media"))
