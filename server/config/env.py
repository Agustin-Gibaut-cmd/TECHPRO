"""Gestión centralizada y segura de variables de entorno para TECHPRO.

Encapsula la carga de variables desde .env evitando acoplar settings.py con la
librería dotenv o con llamadas repetitivas y propensas a error de os.getenv.
Proporciona tipado estricto, valores por defecto seguros y validación de seguridad.
"""

import os
from pathlib import Path
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

MIN_SECRET_LENGTH = 50


def init_environment(base_dir: Path) -> None:
    """Carga de forma segura el archivo .env si existe en el directorio base."""
    env_path = base_dir / ".env"
    if env_path.is_file():
        load_dotenv(env_path)


def env_str(name: str, default: str = "") -> str:
    """Retorna una variable de entorno como texto recortando espacios."""
    return os.getenv(name, default).strip()


def env_bool(name: str, default: bool = False) -> bool:
    """Parsea una variable de entorno como booleano de forma estricta."""
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ImproperlyConfigured(f"{name} debe ser un valor booleano ('true' o 'false').")


def env_int(name: str, default: int) -> int:
    """Parsea una variable de entorno como número entero."""
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value.strip())
    except ValueError as error:
        raise ImproperlyConfigured(f"{name} debe ser un número entero válido.") from error


def env_list(name: str, default: str = "") -> list[str]:
    """Parsea una lista separada por comas descartando elementos vacíos."""
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def load_secret_keys() -> tuple[str, str]:
    """Obtiene y valida exhaustivamente las claves secretas de Django y JWT.

    Garantiza una longitud criptográficamente segura (mínimo 50 caracteres),
    rechaza marcadores de posición predeterminados y exige que ambas claves sean distintas.
    """
    secret_key = env_str("DJANGO_SECRET_KEY")
    if (
        not secret_key
        or secret_key.startswith("replace-with-")
        or len(secret_key) < MIN_SECRET_LENGTH
    ):
        raise ImproperlyConfigured(
            "Definí DJANGO_SECRET_KEY en server/.env con un secreto aleatorio de al menos 50 caracteres."
        )

    jwt_key = env_str("JWT_SIGNING_KEY")
    if (
        not jwt_key
        or jwt_key.startswith("replace-with-")
        or len(jwt_key) < MIN_SECRET_LENGTH
        or jwt_key == secret_key
    ):
        raise ImproperlyConfigured(
            "Definí JWT_SIGNING_KEY en server/.env con un secreto aleatorio distinto de DJANGO_SECRET_KEY."
        )

    return secret_key, jwt_key


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
    """Ejecuta una auditoría de seguridad obligatoria cuando el entorno opera en producción."""
    if debug:
        return

    if secret_key.startswith("dev-") or jwt_key.startswith("dev-"):
        raise ImproperlyConfigured("Usá secretos aleatorios propios para producción.")

    if not allowed_hosts or "*" in allowed_hosts:
        raise ImproperlyConfigured(
            "Definí DJANGO_ALLOWED_HOSTS con los dominios reales en producción."
        )

    for origin in cors_origins + csrf_origins:
        lower_origin = origin.lower()
        if lower_origin.startswith(("http://localhost", "http://127.0.0.1")):
            raise ImproperlyConfigured(
                "Quitá los orígenes locales de CORS_ALLOWED_ORIGINS y CSRF_TRUSTED_ORIGINS en producción."
            )
        if not lower_origin.startswith("https://"):
            raise ImproperlyConfigured(
                "Usá orígenes HTTPS en CORS_ALLOWED_ORIGINS y CSRF_TRUSTED_ORIGINS en producción."
            )

        parsed = urlsplit(origin)
        if (
            "*" in origin
            or not parsed.netloc
            or parsed.path
            or parsed.query
            or parsed.fragment
            or parsed.username
            or parsed.password
        ):
            raise ImproperlyConfigured(
                "Configurá orígenes HTTPS exactos, sin comodines ni rutas."
            )

    if not ssl_redirect:
        raise ImproperlyConfigured("Activá SECURE_SSL_REDIRECT en producción.")

    if hsts_seconds <= 0:
        raise ImproperlyConfigured("Configurá SECURE_HSTS_SECONDS mayor a cero en producción.")

    if hsts_preload and (not hsts_subdomains or hsts_seconds < 31536000):
        raise ImproperlyConfigured(
            "HSTS preload requiere incluir subdominios y al menos un año de HSTS."
        )
