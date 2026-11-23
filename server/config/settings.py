"""Configuración principal de Django para TECHPRO.

Estructurado bajo principios de Clean Code: altamente declarativo, modular y legible.
La gestión de variables de entorno, validaciones criptográficas y construcción
de base de datos se delegan a módulos especializados (config.env y config.database).
"""

from datetime import timedelta
from pathlib import Path

from .database import build_database_config
from .env import (
    env_bool,
    env_int,
    env_list,
    env_str,
    init_environment,
    load_secret_keys,
    validate_production_settings,
)

# --- Rutas base e inicialización de entorno ---
BASE_DIR = Path(__file__).resolve().parent.parent
init_environment(BASE_DIR)

# --- Seguridad y Modo de Ejecución ---
SECRET_KEY, JWT_SIGNING_KEY = load_secret_keys()
DEBUG = env_bool("DEBUG", False)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1" if DEBUG else "")

# --- Aplicaciones Instaladas ---
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "accounts",
    "repairs",
    "workshop",
]

# --- Middleware ---
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "config.middleware.ApiNoStoreMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --- Base de Datos (PostgreSQL en producción, SQLite configurable en local/test) ---
DATABASES = {"default": build_database_config(BASE_DIR, DEBUG)}

# --- Autenticación y Complejidad de Contraseñas ---
AUTH_PASSWORD_MIN_LENGTH = env_int("AUTH_PASSWORD_MIN_LENGTH", 12)
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": AUTH_PASSWORD_MIN_LENGTH},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internacionalización ---
LANGUAGE_CODE = env_str("LANGUAGE_CODE", "es-ar")
TIME_ZONE = env_str("TIME_ZONE", "America/Argentina/Buenos_Aires")
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Políticas CORS y CSRF ---
LOCAL_ORIGINS = "http://localhost:4200,http://127.0.0.1:4200"
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", LOCAL_ORIGINS if DEBUG else "")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", LOCAL_ORIGINS if DEBUG else "")
CORS_ALLOW_CREDENTIALS = True

# --- Django REST Framework (DRF) y Throttling ---
THROTTLE_RATE_ANON = env_str("THROTTLE_RATE_ANON", "30/minute")
THROTTLE_RATE_USER = env_str("THROTTLE_RATE_USER", "120/minute")
THROTTLE_RATE_LOGIN = env_str("THROTTLE_RATE_LOGIN", "5/minute")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "accounts.authentication.CookieJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": THROTTLE_RATE_ANON,
        "user": THROTTLE_RATE_USER,
        "login": THROTTLE_RATE_LOGIN,
    },
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

# --- Autenticación JWT en Cookies HttpOnly ---
JWT_ACCESS_MINUTES = env_int("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", 15)
JWT_REFRESH_DAYS = env_int("JWT_REFRESH_TOKEN_LIFETIME_DAYS", 7)

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=JWT_ACCESS_MINUTES),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=JWT_REFRESH_DAYS),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "SIGNING_KEY": JWT_SIGNING_KEY,
}

# --- Parámetros de Cookies de Sesión y CSRF ---
API_PREFIX = env_str("API_PREFIX", "/api/")
AUTH_ACCESS_COOKIE = env_str("AUTH_ACCESS_COOKIE", "access_token")
AUTH_REFRESH_COOKIE = env_str("AUTH_REFRESH_COOKIE", "refresh_token")
AUTH_ACCESS_COOKIE_PATH = env_str("AUTH_ACCESS_COOKIE_PATH", "/api/")
AUTH_REFRESH_COOKIE_PATH = env_str("AUTH_REFRESH_COOKIE_PATH", "/api/auth/")
AUTH_COOKIE_SECURE = not DEBUG
AUTH_COOKIE_SAMESITE = env_str("AUTH_COOKIE_SAMESITE", "Lax")

CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_PATH = env_str("CSRF_COOKIE_PATH", "/api/")
CSRF_COOKIE_SAMESITE = env_str("CSRF_COOKIE_SAMESITE", "Lax")
CSRF_COOKIE_SECURE = not DEBUG

# --- Encabezados de Seguridad y HSTS ---
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = env_str("SECURE_REFERRER_POLICY", "same-origin")
X_FRAME_OPTIONS = env_str("X_FRAME_OPTIONS", "DENY")
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", not DEBUG)

TRUST_X_FORWARDED_PROTO = env_bool("TRUST_X_FORWARDED_PROTO", False)
SECURE_PROXY_SSL_HEADER = (
    ("HTTP_X_FORWARDED_PROTO", "https") if TRUST_X_FORWARDED_PROTO else None
)

SECURE_HSTS_SECONDS = env_int("SECURE_HSTS_SECONDS", 0 if DEBUG else 31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", False)
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", False)

# --- Parámetros de Reportes y Estadísticas ---
REPORT_MONTHS_WINDOW = env_int("REPORT_MONTHS_WINDOW", 6)
REPORT_TOP_PRODUCTS_LIMIT = env_int("REPORT_TOP_PRODUCTS_LIMIT", 5)

# --- Validación de Políticas de Seguridad en Producción ---
validate_production_settings(
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
