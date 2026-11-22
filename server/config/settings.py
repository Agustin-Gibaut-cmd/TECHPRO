import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ImproperlyConfigured(f"{name} debe ser un valor booleano.")


def env_list(name: str, default: str = "") -> list[str]:
    return [value.strip() for value in os.getenv(name, default).split(",") if value.strip()]


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if (
    not SECRET_KEY
    or SECRET_KEY.startswith("replace-with-")
    or len(SECRET_KEY) < 50
):
    raise ImproperlyConfigured(
        "Definí DJANGO_SECRET_KEY en server/.env con un secreto aleatorio de al menos 50 caracteres."
    )

JWT_SIGNING_KEY = os.getenv("JWT_SIGNING_KEY")
if (
    not JWT_SIGNING_KEY
    or JWT_SIGNING_KEY.startswith("replace-with-")
    or len(JWT_SIGNING_KEY) < 50
    or JWT_SIGNING_KEY == SECRET_KEY
):
    raise ImproperlyConfigured(
        "Definí JWT_SIGNING_KEY en server/.env con un secreto aleatorio distinto de DJANGO_SECRET_KEY."
    )

DEBUG = env_bool("DEBUG", False)
ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    "localhost,127.0.0.1" if DEBUG else "",
)

if not DEBUG:
    if SECRET_KEY.startswith("dev-") or JWT_SIGNING_KEY.startswith("dev-"):
        raise ImproperlyConfigured("Usá secretos aleatorios propios para producción.")
    if not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS:
        raise ImproperlyConfigured(
            "Definí DJANGO_ALLOWED_HOSTS con los dominios reales en producción."
        )

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "accounts",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DB_ENGINE = os.getenv("DB_ENGINE", "postgresql").strip().lower()
DB_SSLMODE = os.getenv("DB_SSLMODE", "prefer").strip().lower()
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
if DB_ENGINE == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
elif DB_ENGINE == "postgresql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "workshop"),
            "USER": os.getenv("DB_USER", "workshop"),
            "PASSWORD": DB_PASSWORD,
            "HOST": os.getenv("DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("DB_PORT", "5432"),
            "CONN_MAX_AGE": 60,
            "OPTIONS": {"sslmode": DB_SSLMODE},
        }
    }
else:
    raise ImproperlyConfigured("DB_ENGINE debe ser 'sqlite' o 'postgresql'.")

if not DEBUG and DB_ENGINE != "postgresql":
    raise ImproperlyConfigured("Usá PostgreSQL cuando DEBUG=false.")
if not DEBUG and DB_SSLMODE not in {"require", "verify-ca", "verify-full"}:
    raise ImproperlyConfigured(
        "En producción, DB_SSLMODE debe exigir una conexión TLS con PostgreSQL."
    )
if DB_ENGINE == "postgresql" and not DB_PASSWORD:
    raise ImproperlyConfigured("Definí DB_PASSWORD para la conexión PostgreSQL.")

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-ar"
TIME_ZONE = "America/Argentina/Buenos_Aires"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOCAL_CORS_ORIGINS = "http://localhost:4200,http://127.0.0.1:4200"
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    LOCAL_CORS_ORIGINS if DEBUG else "",
)
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS",
    LOCAL_CORS_ORIGINS if DEBUG else "",
)
if not DEBUG and any(
    origin.lower().startswith(("http://localhost", "http://127.0.0.1"))
    for origin in CORS_ALLOWED_ORIGINS + CSRF_TRUSTED_ORIGINS
):
    raise ImproperlyConfigured(
        "Quitá los orígenes locales de CORS_ALLOWED_ORIGINS y "
        "CSRF_TRUSTED_ORIGINS en producción."
    )
if not DEBUG and any(
    not origin.lower().startswith("https://")
    for origin in CORS_ALLOWED_ORIGINS + CSRF_TRUSTED_ORIGINS
):
    raise ImproperlyConfigured(
        "Usá orígenes HTTPS en CORS_ALLOWED_ORIGINS y "
        "CSRF_TRUSTED_ORIGINS en producción."
    )

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
        "anon": "30/minute",
        "user": "120/minute",
    },
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "SIGNING_KEY": JWT_SIGNING_KEY,
}

SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", not DEBUG)
if not DEBUG and not SECURE_SSL_REDIRECT:
    raise ImproperlyConfigured("Activá SECURE_SSL_REDIRECT en producción.")
TRUST_X_FORWARDED_PROTO = env_bool("TRUST_X_FORWARDED_PROTO", False)
SECURE_PROXY_SSL_HEADER = (
    ("HTTP_X_FORWARDED_PROTO", "https") if TRUST_X_FORWARDED_PROTO else None
)
AUTH_ACCESS_COOKIE = "access_token"
AUTH_REFRESH_COOKIE = "refresh_token"
AUTH_ACCESS_COOKIE_PATH = "/api/"
AUTH_REFRESH_COOKIE_PATH = "/api/auth/"
AUTH_COOKIE_SECURE = not DEBUG
AUTH_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_PATH = "/api/"
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = int(
    os.getenv("SECURE_HSTS_SECONDS", "0" if DEBUG else "31536000")
)
if not DEBUG and SECURE_HSTS_SECONDS <= 0:
    raise ImproperlyConfigured(
        "Configurá SECURE_HSTS_SECONDS mayor a cero en producción."
    )
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS",
    False,
)
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", False)
if SECURE_HSTS_PRELOAD and (
    not SECURE_HSTS_INCLUDE_SUBDOMAINS or SECURE_HSTS_SECONDS < 31536000
):
    raise ImproperlyConfigured(
        "HSTS preload requiere incluir subdominios y al menos un año de HSTS."
    )
