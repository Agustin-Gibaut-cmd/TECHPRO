"""Configuración principal de Django para TECHPRO."""

from pathlib import Path

from .env import env_bool, env_int, env_list, env_str, init_environment, load_secret_keys, validate_production_settings

BASE_DIR = Path(__file__).resolve().parent.parent
init_environment(BASE_DIR)

from .settings_apps import *
from .settings_auth import *
from .settings_business import *
from .settings_cookies import *
from .settings_database import *
from .settings_http import *
from .settings_i18n import *
from .settings_jwt import *
from .settings_logging import *
from .settings_rest import *

ENVIRONMENT = env_str("ENVIRONMENT", "production").lower()
DEBUG = env_bool("DEBUG", False)
SECRET_KEY, JWT_SIGNING_KEY = load_secret_keys()
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1" if DEBUG else "")

DATA_UPLOAD_MAX_MEMORY_SIZE = env_int("DATA_UPLOAD_MAX_MEMORY_SIZE", 1_048_576)
FILE_UPLOAD_MAX_MEMORY_SIZE = env_int("FILE_UPLOAD_MAX_MEMORY_SIZE", 2_621_440)
DATA_UPLOAD_MAX_NUMBER_FIELDS = env_int("DATA_UPLOAD_MAX_NUMBER_FIELDS", 250)

API_PREFIX = env_str("API_PREFIX", "/api/")

validate_production_settings(
    environment=ENVIRONMENT,
    debug=DEBUG,
    secret_key=SECRET_KEY,
    jwt_key=JWT_SIGNING_KEY,
    allowed_hosts=ALLOWED_HOSTS,
    cors_origins=CORS_ALLOWED_ORIGINS,
    csrf_origins=CSRF_TRUSTED_ORIGINS,
    ssl_redirect=SECURE_SSL_REDIRECT,
    hsts_seconds=SECURE_HSTS_SECONDS,
    hsts_preload=SECURE_HSTS_PRELOAD,
    hsts_subdomains=SECURE_HSTS_INCLUDE_SUBDOMAINS,
)
