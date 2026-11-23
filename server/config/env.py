"""Gestión centralizada, tipada y endurecida de variables de entorno para TECHPRO.

Responsabilidades:
- Cargar variables desde `.env` de forma segura sin acoplar `settings.py` a `python-dotenv`.
- Proveer parsers estrictos (`env_str`, `env_bool`, `env_int`, `env_list`) con validación de tipos.
- Auditar secretos criptográficos (longitud y entropía mínima) y reglas de red/TLS antes
  de permitir que la aplicación inicie en entornos productivos.
"""

from datetime import timedelta
from ipaddress import ip_address
import os
from pathlib import Path
import secrets
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

VALID_ENVIRONMENTS = frozenset({"development", "test", "staging", "production"})
TRUTHY_VALUES = frozenset({"1", "true", "yes", "on"})
FALSY_VALUES = frozenset({"0", "false", "no", "off"})
INSECURE_PREFIXES = ("replace-with-", "dev-", "changeme", "secret", "test-")
MIN_UNIQUE_SECRET_CHARS = 12


# 1. INICIALIZACIÓN Y PARSERS TIPADOS
def init_environment(base_dir: Path) -> None:
    """Carga el archivo `.env` desde el directorio base si existe."""
    if (env_path := base_dir / ".env").is_file():
        load_dotenv(env_path)


def env_str(name: str, default: str = "") -> str:
    """Obtiene una variable de entorno como cadena limpia de espacios laterales."""
    return os.getenv(name, default).strip()


def env_bool(name: str, default: bool = False) -> bool:
    """Parsea estrictamente una variable booleana aceptando formatos estándar."""
    if (val := os.getenv(name)) is None:
        return default
    norm = val.strip().lower()
    if norm in TRUTHY_VALUES:
        return True
    if norm in FALSY_VALUES:
        return False
    raise ImproperlyConfigured(f"{name} debe ser un valor booleano ('true' o 'false').")


def env_int(name: str, default: int) -> int:
    """Parsea estrictamente una variable numérica entera."""
    if (val := os.getenv(name)) is None:
        return default
    try:
        return int(val.strip())
    except ValueError as err:
        raise ImproperlyConfigured(f"{name} debe ser un número entero válido.") from err


def env_list(name: str, default: str = "") -> list[str]:
    """Parsea una lista separada por comas omitiendo entradas vacías."""
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


# 2. VALIDACIÓN CRIPTOGRÁFICA DE CLAVES
def _validate_secret_entropy(name: str, value: str, min_len: int) -> None:
    """Verifica longitud mínima, ausencia de prefijos inseguros y diversidad de caracteres."""
    lower_val = value.lower()
    if (
        not value
        or lower_val.startswith(INSECURE_PREFIXES)
        or len(value) < min_len
        or len(set(value)) < MIN_UNIQUE_SECRET_CHARS
    ):
        raise ImproperlyConfigured(
            f"Definí {name} en server/.env con un secreto aleatorio fuerte "
            f"(mínimo {min_len} caracteres y alta entropía)."
        )


def load_secret_keys() -> tuple[str, str]:
    """Carga y audita las claves de firma de Django y SimpleJWT."""
    min_len = env_int("MIN_SECRET_LENGTH", len(secrets.token_urlsafe()))
    secret_key = env_str("DJANGO_SECRET_KEY")
    jwt_key = env_str("JWT_SIGNING_KEY")

    _validate_secret_entropy("DJANGO_SECRET_KEY", secret_key, min_len)
    _validate_secret_entropy("JWT_SIGNING_KEY", jwt_key, min_len)

    if jwt_key == secret_key:
        raise ImproperlyConfigured("JWT_SIGNING_KEY debe ser criptográficamente distinto de DJANGO_SECRET_KEY.")

    return secret_key, jwt_key


# 3. AUDITORÍA DE RED, ORÍGENES Y SEGURIDAD EN PRODUCCIÓN
def _is_non_public_host(hostname: str | None) -> bool:
    """Detecta hostnames locales, loopback o direcciones IP privadas/reservadas."""
    if not hostname:
        return True
    lower_host = hostname.lower()
    if lower_host == "localhost" or lower_host.endswith(".local"):
        return True
    try:
        ip = ip_address(lower_host)
        return ip.is_loopback or ip.is_private or ip.is_reserved or ip.is_unspecified
    except ValueError:
        return False


def _validate_origin(origin: str) -> None:
    """Exige orígenes HTTPS puros, públicos y sin rutas, credenciales ni comodines."""
    parsed = urlsplit(origin)
    if _is_non_public_host(parsed.hostname):
        raise ImproperlyConfigured(f"Origen local o privado no permitido en producción: '{origin}'.")
    if parsed.scheme.lower() != "https":
        raise ImproperlyConfigured(f"Solo se permiten orígenes HTTPS en producción: '{origin}'.")
    if (
        "*" in origin
        or not parsed.netloc
        or any((parsed.path, parsed.query, parsed.fragment, parsed.username, parsed.password))
    ):
        raise ImproperlyConfigured(
            f"Configurá orígenes HTTPS exactos sin comodines, rutas ni credenciales: '{origin}'."
        )


def validate_production_settings(
    environment: str,
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
    """Audita la configuración completa antes de permitir el arranque en producción."""
    if environment not in VALID_ENVIRONMENTS:
        raise ImproperlyConfigured(
            f"ENVIRONMENT='{environment}' inválido. Valores permitidos: {', '.join(sorted(VALID_ENVIRONMENTS))}."
        )

    if environment == "production" and debug:
        raise ImproperlyConfigured("CRÍTICO: DEBUG no puede estar activo cuando ENVIRONMENT=production.")

    if debug:
        return

    if secret_key.lower().startswith(INSECURE_PREFIXES) or jwt_key.lower().startswith(INSECURE_PREFIXES):
        raise ImproperlyConfigured("Usá secretos aleatorios propios de producción.")

    if not allowed_hosts or any(h == "*" or _is_non_public_host(h.lstrip(".")) for h in allowed_hosts):
        raise ImproperlyConfigured("Definí DJANGO_ALLOWED_HOSTS únicamente con dominios públicos reales.")

    for origin in cors_origins + csrf_origins:
        _validate_origin(origin)

    if not ssl_redirect:
        raise ImproperlyConfigured("Activá SECURE_SSL_REDIRECT en producción.")

    if hsts_seconds <= 0:
        raise ImproperlyConfigured("Configurá SECURE_HSTS_SECONDS mayor a cero en producción.")

    one_year = int(timedelta(days=365).total_seconds())
    min_hsts = env_int("MIN_HSTS_PRELOAD_SECONDS", one_year)
    if hsts_preload and (not hsts_subdomains or hsts_seconds < min_hsts):
        raise ImproperlyConfigured(
            f"HSTS preload requiere incluir subdominios y al menos {min_hsts} segundos de vigencia."
        )