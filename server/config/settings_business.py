"""Parámetros de negocio."""

from .env import env_int

REPORT_MONTHS_WINDOW = env_int("REPORT_MONTHS_WINDOW", 6)
REPORT_TOP_PRODUCTS_LIMIT = env_int("REPORT_TOP_PRODUCTS_LIMIT", 5)
