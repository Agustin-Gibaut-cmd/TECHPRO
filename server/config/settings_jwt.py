"""Configuración JWT en cookies."""

from datetime import timedelta

from .env import env_int, load_secret_keys

_, JWT_SIGNING_KEY = load_secret_keys()

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
