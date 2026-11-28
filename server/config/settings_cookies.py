"""Cookies de sesión y CSRF."""

from .env import env_bool, env_str
from .settings_http import DEBUG

AUTH_ACCESS_COOKIE = env_str("AUTH_ACCESS_COOKIE", "access_token")
AUTH_REFRESH_COOKIE = env_str("AUTH_REFRESH_COOKIE", "refresh_token")
AUTH_ACCESS_COOKIE_PATH = env_str("AUTH_ACCESS_COOKIE_PATH", "/api/")
AUTH_REFRESH_COOKIE_PATH = env_str("AUTH_REFRESH_COOKIE_PATH", "/api/auth/")

AUTH_COOKIE_SECURE = not DEBUG
AUTH_COOKIE_SAMESITE = env_str("AUTH_COOKIE_SAMESITE", "Lax")
