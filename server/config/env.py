"""Gestión centralizada y segura de variables de entorno para TECHPRO."""

from datetime import timedelta
from ipaddress import ip_address
import os
from pathlib import Path
import secrets
from urllib.parse import urlsplit
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv


def init_environment(base_dir: Path) -> None:
    if (env_path := base_dir / ".env").is_file():
        load_dotenv(env_path)


def env_str(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def env_bool(name: str, default: bool = False) -> bool:
    if (val := os.getenv(name)) is None:
        return default
    norm = val.strip().lower()
    if norm in {"1", "true", "yes", "on"}:
        return True
    if norm in {"0", "false", "no", "off"}:
        return False
    raise ImproperlyConfigured(f"{name} debe ser un booleano ('true' o 'false').")


def env_int(name: str, default: int) -> int:
    if (val := os.getenv(name)) is None:
        return default
    try:
        return int(val.strip())
    except ValueError as err:
        raise ImproperlyConfigured(f"{name} debe ser un entero válido.") from err


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


def load_secret_keys() -> tuple[str, str]:
    min_len = env_int("MIN_SECRET_LENGTH", len(secrets.token_urlsafe()))
    secret_key, jwt_key = env_str("DJANGO_SECRET_KEY"), env_str("JWT_SIGNING_KEY")
    for name, val in (("DJANGO_SECRET_KEY", secret_key), ("JWT_SIGNING_KEY", jwt_key)):
        if not val or val.startswith("replace-with-") or len(val) < min_len:
            raise ImproperlyConfigured(f"Definí {name} en server/.env con al menos {min_len} caracteres.")
    if jwt_key == secret_key:
        raise ImproperlyConfigured("JWT_SIGNING_KEY debe ser distinto de DJANGO_SECRET_KEY.")
    return secret_key, jwt_key


def _is_local_host(hostname: str | None) -> bool:
    if not hostname or hostname == "localhost":
        return True
    try:
        return ip_address(hostname).is_loopback
    except ValueError:
        return False


def _validate_origin(origin: str) -> None:
    p = urlsplit(origin)
    if _is_local_host(p.hostname):
        raise ImproperlyConfigured("Quitá orígenes locales de CORS/CSRF en producción.")
    if p.scheme.lower() != "https":
        raise ImproperlyConfigured("Usá orígenes HTTPS en CORS/CSRF en producción.")
    if "*" in origin or not p.netloc or any((p.path, p.query, p.fragment, p.username, p.password)):
        raise ImproperlyConfigured("Configurá orígenes HTTPS exactos, sin comodines ni rutas.")


def validate_production_settings(
    debug: bool,
    secret_key: str,
    jwt_key: str,
    allowed_hosts: list[str],
    cors_origins: list[str],
    csrf_origins: list[str],
    ssl_redirect: bool,
    hsts_seconds: int,
    hsts_preload: bool,
    hsts_subdomains: bool,
) -> None:
    if debug:
        return
    if secret_key.startswith("dev-") or jwt_key.startswith("dev-"):
        raise ImproperlyConfigured("Usá secretos aleatorios propios para producción.")
    if not allowed_hosts or "*" in allowed_hosts:
        raise ImproperlyConfigured("Definí DJANGO_ALLOWED_HOSTS con dominios reales en producción.")
    for origin in cors_origins + csrf_origins:
        _validate_origin(origin)
    if not ssl_redirect:
        raise ImproperlyConfigured("Activá SECURE_SSL_REDIRECT en producción.")
    if hsts_seconds <= 0:
        raise ImproperlyConfigured("Configurá SECURE_HSTS_SECONDS mayor a cero en producción.")

    one_year = int(timedelta(days=365).total_seconds())
    min_hsts = env_int("MIN_HSTS_PRELOAD_SECONDS", one_year)
    if hsts_preload and (not hsts_subdomains or hsts_seconds < min_hsts):
        raise ImproperlyConfigured(f"HSTS preload requiere subdominios y al menos {min_hsts} segundos de HSTS.")