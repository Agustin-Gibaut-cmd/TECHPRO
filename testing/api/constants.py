"""Constantes compartidas por los smoke tests de la API."""

import os

DEFAULT_API_URL = "http://127.0.0.1:8000"
DEFAULT_ADMIN_EMAIL = "admin@techpro.local"
DEFAULT_TEST_PASSWORD = "TechproTest!2026"
DEFAULT_READ_ONLY_EMAIL = "consulta@techpro.local"

REPAIR_SMOKE_PAYLOAD = {
    "customer_name": "Cliente API",
    "customer_phone": "+54 11 1234-5678",
    "device_type": "Notebook",
    "device_model": "API Test",
    "serial_number": "api-001",
    "issue_description": "Prueba de humo de la API.",
    "status": "received",
}


def api_url() -> str:
    return os.getenv("TECHPRO_API_URL", DEFAULT_API_URL)


def admin_email() -> str:
    return os.getenv("TECHPRO_TEST_EMAIL", DEFAULT_ADMIN_EMAIL)


def test_password() -> str:
    return os.getenv("TECHPRO_TEST_PASSWORD", DEFAULT_TEST_PASSWORD)


def read_only_email() -> str:
    return os.getenv("TECHPRO_READ_ONLY_EMAIL", DEFAULT_READ_ONLY_EMAIL)
