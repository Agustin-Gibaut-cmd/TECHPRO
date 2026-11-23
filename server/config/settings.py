"""Configuración principal y endurecida (Hardened) de Django para TECHPRO.

Diseñada bajo principios de Defensa en Profundidad (Defense in Depth) y Clean Code:
- Fail-safe por defecto: inicia en modo producción restrictivo si falta configuración.
- Cero secretos hardcoded: apto para repositorios públicos en GitHub.
- Validación criptográfica y de red delegada a `config.env` y `config.database`.
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

# 1. RUTAS BASE E INICIALIZACIÓN DE ENTORNO
BASE_DIR = Path(__file__).resolve().parent.parent
init_environment(BASE_DIR)

# 2. MODO DE EJECUCIÓN, IDENTIDAD DEL ENTORNO Y CLAVES CRIPTOGRÁFICAS
ENVIRONMENT = env_str("ENVIRONMENT", "production").lower()
DEBUG = env_bool("DEBUG", False)
SECRET_KEY, JWT_SIGNING_KEY = load_secret_keys()

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1" if DEBUG else "")

# ==============================================================================
# 3. APLICACIONES Y MIDDLEWARES (Superficie de ataque mínima)
# ==============================================================================
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

# 4. BASE DE DATOS
# 
DATABASES = {"default": build_database_config(BASE_DIR, DEBUG)}

# 5. AUTENTICACIÓN, HASHING Y POLÍTICA DE CONTRASEÑAS
# Prioriza Argon2 / PBKDF2 robusto para almacenamiento de contraseñas
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
]

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

# 6. INTERNACIONALIZACIÓN Y ZONA HORARIA
LANGUAGE_CODE = env_str("LANGUAGE_CODE", "es-ar")
TIME_ZONE = env_str("TIME_ZONE", "America/Argentina/Buenos_Aires")
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# 7. POLÍTICAS CORS Y CSRF (Aislamiento Cross-Origin)
LOCAL_DEV_ORIGINS = "http://localhost:4200,http://127.0.0.1:4200"
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", LOCAL_DEV_ORIGINS if DEBUG else "")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", LOCAL_DEV_ORIGINS if DEBUG else "")

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS = [
    "accept",
    "authorization",
    "content-type",
    "origin",
    "x-csrftoken",
    "x-requested-with",
]
CORS_PREFLIGHT_MAX_AGE = env_int("CORS_PREFLIGHT_MAX_AGE", 86400)

# 8. LÍMITES DE PAYLOAD (Mitigación DoS / Agotamiento de Memoria)
DATA_UPLOAD_MAX_MEMORY_SIZE = env_int("DATA_UPLOAD_MAX_MEMORY_SIZE", 1_048_576)  # 1 MB máx.
FILE_UPLOAD_MAX_MEMORY_SIZE = env_int("FILE_UPLOAD_MAX_MEMORY_SIZE", 2_621_440)  # 2.5 MB máx.
DATA_UPLOAD_MAX_NUMBER_FIELDS = env_int("DATA_UPLOAD_MAX_NUMBER_FIELDS", 250)

# 9. DJANGO REST FRAMEWORK (DRF) Y RATE LIMITING (Throttling)
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
        "anon": env_str("THROTTLE_RATE_ANON", "30/minute"),
        "user": env_str("THROTTLE_RATE_USER", "120/minute"),
        "login": env_str("THROTTLE_RATE_LOGIN", "5/minute"),
    },
    # Solo JSON en respuestas: evita exposición de interfaz web navegable en producción
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "EXCEPTION_HANDLER": "rest_framework.views.exception_handler",
}

# 10. AUTENTICACIÓN JWT EN COOKIES HTTPONLY
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env_int("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", 15)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env_int("JWT_REFRESH_TOKEN_LIFETIME_DAYS", 7)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": JWT_SIGNING_KEY,
    "LEEWAY": timedelta(seconds=env_int("JWT_LEEWAY_SECONDS", 10)),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# 11. COOKIES DE SESIÓN Y CSRF (Blindaje contra XSS y CSRF)
API_PREFIX = env_str("API_PREFIX", "/api/")
AUTH_ACCESS_COOKIE = env_str("AUTH_ACCESS_COOKIE", "access_token")
AUTH_REFRESH_COOKIE = env_str("AUTH_REFRESH_COOKIE", "refresh_token")
AUTH_ACCESS_COOKIE_PATH = env_str("AUTH_ACCESS_COOKIE_PATH", "/api/")
AUTH_REFRESH_COOKIE_PATH = env_str("AUTH_REFRESH_COOKIE_PATH", "/api/auth/")

AUTH_COOKIE_SECURE = not DEBUG
AUTH_COOKIE_SAMESITE = env_str("AUTH_COOKIE_SAMESITE", "Lax")

# Nota: Si el frontend SPA lee la cookie CSRF vía JS, configurar CSRF_COOKIE_HTTPONLY=False
CSRF_COOKIE_HTTPONLY = env_bool("CSRF_COOKIE_HTTPONLY", True)
CSRF_COOKIE_PATH = env_str("CSRF_COOKIE_PATH", "/api/")
CSRF_COOKIE_SAMESITE = env_str("CSRF_COOKIE_SAMESITE", "Lax")
CSRF_COOKIE_SECURE = not DEBUG
CSRF_USE_SESSIONS = False

# 12. ENCABEZADOS DE SEGURIDAD HTTP, TLS Y HSTS
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
SECURE_REFERRER_POLICY = env_str("SECURE_REFERRER_POLICY", "strict-origin-when-cross-origin")
X_FRAME_OPTIONS = env_str("X_FRAME_OPTIONS", "DENY")

SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", not DEBUG)
TRUST_X_FORWARDED_PROTO = env_bool("TRUST_X_FORWARDED_PROTO", False)
SECURE_PROXY_SSL_HEADER = (
    ("HTTP_X_FORWARDED_PROTO", "https") if TRUST_X_FORWARDED_PROTO else None
)

SECURE_HSTS_SECONDS = env_int("SECURE_HSTS_SECONDS", 0 if DEBUG else 31_536_000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", not DEBUG)
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", False)

# 13. LOGGING DE AUDITORÍA Y SEGURIDAD
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "security": {
            "format": "[{asctime}] {levelname} {name} | {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "security",
        },
    },
    "loggers": {
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}

# 14. PARÁMETROS DE NEGOCIO
REPORT_MONTHS_WINDOW = env_int("REPORT_MONTHS_WINDOW", 6)
REPORT_TOP_PRODUCTS_LIMIT = env_int("REPORT_TOP_PRODUCTS_LIMIT", 5)

# 15. AUDITORÍA OBLIGATORIA DE SEGURIDAD AL ARRANCAR
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