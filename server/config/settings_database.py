"""Configuración de base de datos."""

from pathlib import Path

from config.database import build_database_config

from .settings_http import DEBUG

BASE_DIR = Path(__file__).resolve().parents[1]
DATABASES = {"default": build_database_config(BASE_DIR, DEBUG)}
