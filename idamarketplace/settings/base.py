import os
from pathlib import Path

from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Chargement explicite du fichier .env
load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is missing. Set it in your .env file "
        "(see .env.example for a template)."
    )

DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Staging : approuver les annonces automatiquement a la publication (les rend
# visibles tout de suite, sans validation humaine). Defaut : False.
AUTO_APPROVE_ANNOUNCEMENTS = (
    os.getenv("AUTO_APPROVE_ANNOUNCEMENTS", "False").lower() == "true"
)

# URL du frontend Next.js (pour les liens dans les emails, ex. activation).
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

SITE_ID = 1

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.sites",
    "taggit",
    "crispy_forms",
    "crispy_bootstrap5",
    "modeltranslation",
    "marketplace",
    "accounts",
    "evenements",
    "ckeditor",
    "import_export",
    "django_crontab",
    "django_countries",
    "flags",
    "phonenumber_field",
    "drf_spectacular",
    "rest_framework",
    "blog",
    "django_ckeditor_5",
    "axes",
    "django_otp",
    "django_otp.plugins.otp_static",
    "django_otp.plugins.otp_totp",
    "two_factor",
    "corsheaders",
    "anymail",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # OTP doit venir APRES AuthenticationMiddleware
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    # axes doit etre en dernier pour intercepter les tentatives de login
    "axes.middleware.AxesMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            # Frontend public en Next.js — les context_processors custom
            # pour les templates HTML ont ete retires. On garde uniquement
            # les processors requis par admin Django + auth.
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
            ],
        },
    },
]


ROOT_URLCONF = "idamarketplace.urls"
WSGI_APPLICATION = "idamarketplace.wsgi.application"

AUTH_USER_MODEL = "accounts.Utilisateur"

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = LOGIN_URL

LANGUAGE_CODE = "fr"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ("fr", _("Français")),
    ("en", _("English")),
    ("it", _("Italiano")),
]

MODELTRANSLATION_DEFAULT_LANGUAGE = "fr"
MODELTRANSLATION_FALLBACK_LANGUAGES = ("fr", "en", "it")
MODELTRANSLATION_TRANSLATION_FILES = (
    "marketplace.translations",
    "evenements.translations",
    "blog.translations",
)

LOCALE_PATHS = [os.path.join(BASE_DIR, "locale")]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]


MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")


STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"


# STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"


CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# ---------------------------------------------------------------------------
# Securite
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Headers HTTP (defense en profondeur)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"

# Session/CSRF cookies
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # garde False : permet la lecture du token via JS
SESSION_COOKIE_AGE = 60 * 60 * 8  # 8h
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# django-axes : verrouillage anti brute-force
AXES_FAILURE_LIMIT = 5  # apres 5 echecs
AXES_COOLOFF_TIME = 1  # blocage pendant 1h
AXES_LOCKOUT_PARAMETERS = ["ip_address", "username"]
AXES_RESET_ON_SUCCESS = True
AXES_ENABLE_ADMIN = True

# django-two-factor-auth : 2FA TOTP pour l'admin
# Le ModelBackend est requis pour que two_factor authentifie correctement
# (axes.AxesStandaloneBackend ne lit que la requete, pas le user).
LOGIN_URL = "/accounts/login/"  # users normaux gardent leur page
LOGIN_REDIRECT_URL = "/"
TWO_FACTOR_LOGIN_TIMEOUT = 30 * 60  # 30 min entre 2 verifications
TWO_FACTOR_REMEMBER_COOKIE_AGE = 7 * 24 * 60 * 60  # 7 jours "se souvenir"
TWO_FACTOR_TOTP_DIGITS = 6
TWO_FACTOR_QR_FACTORY = "qrcode.image.svg.SvgPathImage"
TWO_FACTOR_CALL_GATEWAY = None  # pas d'appel telephonique
TWO_FACTOR_SMS_GATEWAY = None  # pas de SMS
# Force la 2FA pour l'admin : staff/superuser doivent enroller un device
# au premier login admin (cf. urls.py qui swappe AdminSite).

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "120/min",
        "user": "600/min",
        # Limites strictes sur les endpoints sensibles (anti brute-force /
        # enumeration / grinding de refresh token).
        "auth": "10/min",
        "register": "5/min",
    },
}

# ============================================================
# CORS — pour permettre a Next.js frontend :3000 d'appeler l'API
# ============================================================
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ALLOW_CREDENTIALS = True

# ============================================================
# JWT — durees des tokens (auth Next.js)
# ============================================================
from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=2),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    "ROTATE_REFRESH_TOKENS": True,
    # SECURITE : invalide l'ancien refresh token apres rotation (necessite
    # l'app token_blacklist). Un refresh token vole ne reste plus valide
    # 14 jours apres qu'une rotation legitime a eu lieu.
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "API Événements Marketplace",
    "DESCRIPTION": """
    API complète pour la gestion des événements du marketplace.

    ## Fonctionnalités principales
    - Lister les événements actifs
    - Gérer les inscriptions/désinscriptions
    - Vérifier les participants
    """,
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api/",
    "ENUM_NAME_OVERRIDES": {
        "InteresseChoices": ["true", "false"],
    },
    "EXTENSIONS_INFO": {
        "x-logo": {
            "url": "https://votre-logo.com/logo.png",
            "backgroundColor": "#FFFFFF",
        }
    },
}

# EMAIL_BACKEND = os.getenv("EMAIL_BACKEND")
# EMAIL_HOST = os.getenv("EMAIL_HOST")
# EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS") == "True"
# EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
# EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
# EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
# DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)


# Defaut sur (console) si non defini : evite un EMAIL_BACKEND=None qui fait
# planter send_mail (l'import du backend echoue AVANT fail_silently).
EMAIL_BACKEND = (
    os.getenv("EMAIL_BACKEND")
    or "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS") == "True"
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")

# Envoi via API HTTP (Resend) — contourne le blocage du SMTP sortant sur
# Render (free). Activer en prod avec :
#   EMAIL_BACKEND=anymail.backends.resend.EmailBackend
#   RESEND_API_KEY=re_xxx  (cle API Resend)
# L'expediteur (DEFAULT_FROM_EMAIL) doit etre sur un domaine verifie chez Resend.
ANYMAIL = {
    "RESEND_API_KEY": os.getenv("RESEND_API_KEY", ""),
}

SITE_DOMAIN = os.getenv("SITE_DOMAIN", "http://127.0.0.1:8033")

# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# EMAIL_HOST = os.getenv("EMAIL_HOST")
# EMAIL_PORT = int(os.getenv("EMAIL_PORT"))

# EMAIL_USE_SSL = True
# EMAIL_USE_TLS = True

# EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
# EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")

# DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


# SITE_DOMAIN = os.getenv("SITE_DOMAIN", "nourdignagrimarket.com")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


CRONJOBS = [
    ("*/1 * * * *", "marketplace.cron.validate_products"),
    ("*/2 * * * *", "marketplace.cron.check_product_descriptions"),
    # ('*/3 * * * *', 'marketplace.cron.send_keyword_notifications'),
]


CKEDITOR_BASEPATH = "/static/ckeditor/ckeditor/"
customColorPalette = [
    {"color": "hsl(45, 138%, 74%)", "label": "Green"},
    {"color": "hsl(4, 90%, 58%)", "label": "Red"},
    {"color": "hsl(340, 82%, 52%)", "label": "Pink"},
    {"color": "hsl(291, 64%, 42%)", "label": "Purple"},
    {"color": "hsl(262, 52%, 47%)", "label": "Deep Purple"},
    {"color": "hsl(231, 48%, 48%)", "label": "Indigo"},
    {"color": "hsl(207, 90%, 54%)", "label": "Blue"},
    {"color": "hsl(148, 51%, 36%)", "label": "Green"},
    {"color": "hsl(13, 92%, 57%)", "label": "Orange Red"},
    {"color": "hsl(33, 90%, 54%)", "label": "Orange"},
]


CKEDITOR_5_CONFIGS = {
    "default": {
        "toolbar": {
            "items": [
                "heading",
                "|",
                "bold",
                "italic",
                "link",
                "bulletedList",
                "numberedList",
                "blockQuote",
                "alignment",
                "|",
                "fontSize",
                "fontFamily",  # 👈 bouton choix police
                "fontColor",
                "fontBackgroundColor",
                "|",
                "outdent",  # 👈 retrait gauche
                "indent",  # 👈 retrait droit
                "removeFormat",  # 👈 supprime la mise en forme → paragraphe neutre
                "|",
                "style",
            ],
        },
        "fontSize": {
            "options": [
                9,
                10,
                11,
                12,
                13,
                "default",
                15,
                16,
                17,
                18,
                19,
                21,
                22,
                23,
                24,
                25,
                26,
                27,
                28,
                29,
                30,
            ],
            "supportAllValues": True,
        },
        "style": {
            "definitions": [
                {
                    "name": "Interligne réduit",
                    "element": "p",
                    "classes": ["line-tight"],
                },
                {
                    "name": "Interligne normal",
                    "element": "p",
                    "classes": ["line-normal"],
                },
                {
                    "name": "Interligne large",
                    "element": "p",
                    "classes": ["line-loose"],
                },
            ]
        },
        "fontFamily": {
            "options": [
                "default",
                "Arial, Helvetica, sans-serif",
                "Times New Roman, Times, serif",
                "Calibri, sans-serif",
                "Roboto, sans-serif",
                "Rubik, sans-serif",
            ],
            "supportAllValues": True,
        },
    },
    "extends": {
        "blockToolbar": [
            "paragraph",
            "heading1",
            "heading2",
            "heading3",
            "|",
            "bulletedList",
            "numberedList",
            "|",
            "blockQuote",
            "|",
            "alignment",
            "|",
            "outdent",
            "indent",
            "|",
            "removeFormat",
            "underline",
            "strikethrough",
        ],
        "toolbar": {
            "items": [
                "heading",
                "|",
                "outdent",
                "indent",
                "|",
                "bold",
                "italic",
                "link",
                "underline",
                "strikethrough",
                "code",
                "subscript",
                "superscript",
                "highlight",
                "|",
                "codeBlock",
                "sourceEditing",
                "insertImage",
                "bulletedList",
                "numberedList",
                "todoList",
                "|",
                "blockQuote",
                "imageUpload",
                "|",
                "fontSize",
                "fontFamily",  # 👈 ajouté ici aussi
                "fontColor",
                "fontBackgroundColor",
                "mediaEmbed",
                "removeFormat",
                "insertTable",
                "|",
                "alignment",
                "|",
            ],
            "shouldNotGroupWhenFull": True,
        },
        "image": {
            "toolbar": [
                "imageTextAlternative",
                "|",
                "imageStyle:alignLeft",
                "imageStyle:alignRight",
                "imageStyle:alignCenter",
                "imageStyle:side",
                "|",
            ],
            "styles": [
                "full",
                "side",
                "alignLeft",
                "alignRight",
                "alignCenter",
            ],
        },
        "table": {
            "contentToolbar": [
                "tableColumn",
                "tableRow",
                "mergeTableCells",
                "tableProperties",
                "tableCellProperties",
            ],
            "tableProperties": {
                "borderColors": customColorPalette,
                "backgroundColors": customColorPalette,
            },
            "tableCellProperties": {
                "borderColors": customColorPalette,
                "backgroundColors": customColorPalette,
            },
        },
        "heading": {
            "options": [
                {
                    "model": "paragraph",
                    "title": "Paragraph",
                    "class": "ck-heading_paragraph",
                },
                {
                    "model": "heading1",
                    "view": "h1",
                    "title": "Heading 1",
                    "class": "ck-heading_heading1",
                },
                {
                    "model": "heading2",
                    "view": "h2",
                    "title": "Heading 2",
                    "class": "ck-heading_heading2",
                },
                {
                    "model": "heading3",
                    "view": "h3",
                    "title": "Heading 3",
                    "class": "ck-heading_heading3",
                },
            ]
        },
    },
    "list": {
        "properties": {
            "styles": True,
            "startIndex": True,
            "reversed": True,
        }
    },
    "alignment": {"options": ["left", "center", "right", "justify"]},
}


AFRICAN_COUNTRY_CODES = [
    "DZ",
    "AO",
    "BJ",
    "BW",
    "BF",
    "BI",
    "CM",
    "CV",
    "CF",
    "TD",
    "KM",
    "CG",
    "CD",
    "CI",
    "DJ",
    "EG",
    "GQ",
    "ER",
    "SZ",
    "ET",
    "GA",
    "GM",
    "GH",
    "GN",
    "GW",
    "KE",
    "LS",
    "LR",
    "LY",
    "MG",
    "MW",
    "ML",
    "MR",
    "MU",
    "YT",
    "MA",
    "MZ",
    "NA",
    "NE",
    "NG",
    "RW",
    "RE",
    "ST",
    "SN",
    "SC",
    "SL",
    "SO",
    "ZA",
    "SS",
    "SD",
    "TZ",
    "TG",
    "TN",
    "UG",
    "EH",
    "ZM",
    "ZW",
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
