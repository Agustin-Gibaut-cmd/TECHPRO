"""Constructor y validador de configuración de base de datos para TECHPRO.

Aísla la lógica de conexión para mantener settings.py limpio y declarativo.
Soporta PostgreSQL (producción y desarrollo) y SQLite (desarrollo local y pruebas).
"""

import os
from pathlib import Path
from typing import Any

from django.core.exceptions import ImproperlyConfigured

from .env import env_int


def build_database_config(base_dir: Path, debug: bool) -> dict[str, Any]:
    """Genera el diccionario de configuración para la conexión de base de datos.

    Aplica validaciones estrictas en entornos productivos (obligatoriedad de PostgreSQL,
    contraseñas no vacías y conexiones cifradas con TLS/SSL).
    """
    engine = os.getenv("DB_ENGINE", "postgresql").strip().lower()

    if engine == "sqlite":
        if not debug:
            raise ImproperlyConfigured("Usá PostgreSQL cuando DEBUG=false.")
        db_name = os.getenv("SQLITE_DB_NAME", "db.sqlite3")
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": base_dir / db_name,
        }

    if engine == "postgresql":
        password = os.getenv("DB_PASSWORD", "")
        sslmode = os.getenv("DB_SSLMODE", "prefer").strip().lower()

        if not debug:
            if sslmode not in {"require", "verify-ca", "verify-full"}:
                raise ImproperlyConfigured(
                    "En producción, DB_SSLMODE debe exigir una conexión TLS con PostgreSQL."
                )
            if not password:
                raise ImproperlyConfigured("Definí DB_PASSWORD para la conexión PostgreSQL.")

        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "workshop"),
            "USER": os.getenv("DB_USER", "workshop"),
            "PASSWORD": password,
            "HOST": os.getenv("DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("DB_PORT", "5432"),
            "CONN_MAX_AGE": env_int("DB_CONN_MAX_AGE", 60),
            "OPTIONS": {"sslmode": sslmode},
        }

    raise ImproperlyConfigured("DB_ENGINE debe ser 'sqlite' o 'postgresql'.")
