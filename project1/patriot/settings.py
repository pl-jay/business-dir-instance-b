"""
Django settings for the patriot project.

This configuration uses the built‑in Django template engine and provides a
simple SQLite database. It also sets up static and media directories, and
configures login and logout URLs. Feel free to adjust these settings to
match your environment.
"""

from pathlib import Path
import os
import dj_database_url
from core import context_processors
from patriot.config_loader import get_config
from dotenv import load_dotenv
from django.urls import reverse_lazy

load_dotenv()

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Instance and theme configuration
#
# A unified project can run multiple branded instances from the same code base.
# The instance is selected via the ``INSTANCE_NAME`` environment variable
# (default: ``patriot``).  Branding values such as site name, logos and CSS
# paths are stored in ``config.yaml`` at the project root.  See
# ``patriot/config_loader.py`` for details.

# Determine the current instance name (case‑insensitive) and load its config.
INSTANCE_NAME: str = os.getenv("INSTANCE_NAME", "patriot").strip().lower()
SITE_CONFIG = get_config(INSTANCE_NAME)

# Expose basic site constants as settings so existing code continues to work.
SITE_NAME: str = SITE_CONFIG.get("SITE_NAME", "FRDM")
SITE_LONG_NAME: str = SITE_CONFIG.get(
    "SITE_LONG_NAME", "Freedom Business Directory"
)

# Compute theme-specific directories for templates and static files.  If the
# directories do not exist, Django will simply ignore them.
THEMES_DIR = BASE_DIR / "themes"
THEME_TEMPLATE_DIR = THEMES_DIR / INSTANCE_NAME / "templates"
THEME_STATIC_DIR = THEMES_DIR / INSTANCE_NAME / "static"

# Security settings
# Configure via environment variables for production readiness. Default values are provided for development.
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only")
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() in ("true", "1", "yes")
ALLOWED_HOSTS: list[str] = (
    os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",")
    if os.getenv("DJANGO_ALLOWED_HOSTS")
    else []
)

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Local apps
    "apps.directory.apps.DirectoryConfig",  # core business directory
    "apps.onchain.apps.OnchainConfig",    # on‑chain records
    "apps.promotions.apps.PromotionsConfig", # promotional campaigns
    "apps.ranking.apps.RankingConfig",    # business rankings
    "apps.reviews.apps.ReviewsConfig",    # user reviews
    "apps.usersapp.apps.UsersappConfig",   # user profiles and extra user views
    "apps.wallets.apps.WalletsConfig"
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Add WhiteNoise middleware to serve static files efficiently in production
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "patriot.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Look for templates in the theme directory first, then fall back to the
        # global templates directory.  This allows each instance to override
        # specific templates (e.g. base.html, navbar.html).
        "DIRS": [THEME_TEMPLATE_DIR, BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.site_constants",
            ],
        },
    },
]

WSGI_APPLICATION = "patriot.wsgi.application"

# Database configuration
# Use DATABASE_URL from environment if provided, else fall back to SQLite.
default_db_url = os.getenv("DATABASE_URL")


DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL", "postgres://postgres:postgres@localhost:5432/patriot"),
        conn_max_age=600,
    )
}

# Password validation (disabled for development)
AUTH_PASSWORD_VALIDATORS: list[dict[str, str]] = []

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = os.getenv("TIME_ZONE", "Asia/Colombo")
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
# Include the theme static directory (for per‑instance CSS/images) before the
# global ``static`` directory.  If the theme does not provide its own
# static files, this path may not exist, but Django will ignore it.
STATICFILES_DIRS = [THEME_STATIC_DIR, BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "assets"

# Configure WhiteNoise to compress and cache static files in production
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Authentication URLs
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "directory:list"
LOGOUT_REDIRECT_URL = "directory:list"


# Minimal chain registry / explorers (extend anytime)
CHAINS = {
    "eth":     {"family": "evm", "explorer_tx": "https://etherscan.io/tx/"},
    "polygon": {"family": "evm", "explorer_tx": "https://polygonscan.com/tx/"},
    "bsc":     {"family": "evm", "explorer_tx": "https://bscscan.com/tx/"},
}

# (If not already set)
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
ALLOW_SIGNUP = True
# ``SITE_NAME`` and ``SITE_LONG_NAME`` are defined near the top of this file
# based on the loaded instance configuration.  ``SITE_DESCRIPTION`` remains
# constant for all instances.
SITE_DESCRIPTION = "A decentralized business directory promoting freedom and transparency."


# OIDC / Keycloak settings
LOGIN_URL = 'oidc_authentication_init'
LOGIN_REDIRECT_URL  = reverse_lazy('directory:list')
LOGOUT_REDIRECT_URL = reverse_lazy('directory:list')

AUTHENTICATION_BACKENDS = [
    'apps.accounts.auth_backends.KeycloakOIDCBackend',  # we’ll add this subclass
    'django.contrib.auth.backends.ModelBackend',
]

KEYCLOAK_BASE  = os.getenv('KEYCLOAK_BASE').rstrip('/')
KEYCLOAK_REALM = os.getenv('KEYCLOAK_REALM')
OIDC_RP_CLIENT_ID     = os.getenv('OIDC_RP_CLIENT_ID')
OIDC_RP_CLIENT_SECRET = os.getenv('OIDC_RP_CLIENT_SECRET')

OIDC_OP_ISSUER = f"{KEYCLOAK_BASE}/realms/{KEYCLOAK_REALM}"
OIDC_OP_AUTHORIZATION_ENDPOINT = f"{OIDC_OP_ISSUER}/protocol/openid-connect/auth"
OIDC_OP_TOKEN_ENDPOINT         = f"{OIDC_OP_ISSUER}/protocol/openid-connect/token"
OIDC_OP_USER_ENDPOINT          = f"{OIDC_OP_ISSUER}/protocol/openid-connect/userinfo"
OIDC_OP_JWKS_ENDPOINT          = f"{OIDC_OP_ISSUER}/protocol/openid-connect/certs"
OIDC_OP_LOGOUT_ENDPOINT        = f"{OIDC_OP_ISSUER}/protocol/openid-connect/logout"

OIDC_RP_SIGN_ALGO = 'RS256'
OIDC_RP_SCOPES = 'openid email profile'
OIDC_STORE_ID_TOKEN = True
OIDC_STORE_ACCESS_TOKEN = True
OIDC_VERIFY_SSL = False  # dev only