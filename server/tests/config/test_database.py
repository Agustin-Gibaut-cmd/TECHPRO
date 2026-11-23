"""Pruebas para el constructor y validador de conexiones de base de datos."""

from pathlib import Path
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from config.database import build_database_config


class DatabaseConfigTests(SimpleTestCase):
    """Verifica la generación de configuración para SQLite y PostgreSQL."""

    def setUp(self):
        self.base_dir = Path("/mock/base/dir")

    def test_sqlite_config_generation_in_debug_mode(self):
        """Genera correctamente la configuración de SQLite en modo desarrollo."""
        with patch.dict("os.environ", {"DB_ENGINE": "sqlite", "SQLITE_DB_NAME": "test.sqlite3"}):
            config = build_database_config(self.base_dir, debug=True)
            self.assertEqual(config["ENGINE"], "django.db.backends.sqlite3")
            self.assertEqual(config["NAME"], self.base_dir / "test.sqlite3")

    def test_sqlite_rejected_in_production(self):
        """Rechaza el uso de SQLite cuando DEBUG=False."""
        with patch.dict("os.environ", {"DB_ENGINE": "sqlite"}):
            with self.assertRaises(ImproperlyConfigured):
                build_database_config(self.base_dir, debug=False)

    def test_postgresql_config_generation_in_development(self):
        """Genera configuración de PostgreSQL con parámetros estándar en desarrollo."""
        with patch.dict("os.environ", {
            "DB_ENGINE": "postgresql",
            "DB_NAME": "test_db",
            "DB_USER": "test_user",
            "DB_PASSWORD": "secret_password",
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "DB_SSLMODE": "prefer",
        }):
            config = build_database_config(self.base_dir, debug=True)
            self.assertEqual(config["ENGINE"], "django.db.backends.postgresql")
            self.assertEqual(config["NAME"], "test_db")
            self.assertEqual(config["USER"], "test_user")
            self.assertEqual(config["PASSWORD"], "secret_password")
            self.assertEqual(config["OPTIONS"]["sslmode"], "prefer")

    def test_postgresql_requires_strong_sslmode_in_production(self):
        """En producción (DEBUG=False), rechaza sslmode laxo como 'prefer' o 'disable'."""
        with patch.dict("os.environ", {
            "DB_ENGINE": "postgresql",
            "DB_PASSWORD": "secret_password",
            "DB_SSLMODE": "prefer",
        }):
            with self.assertRaises(ImproperlyConfigured):
                build_database_config(self.base_dir, debug=False)

    def test_postgresql_accepts_valid_tls_sslmode_in_production(self):
        """En producción, acepta sslmode require, verify-ca y verify-full."""
        for valid_mode in ("require", "verify-ca", "verify-full"):
            with patch.dict("os.environ", {
                "DB_ENGINE": "postgresql",
                "DB_PASSWORD": "secret_password",
                "DB_SSLMODE": valid_mode,
            }):
                config = build_database_config(self.base_dir, debug=False)
                self.assertEqual(config["OPTIONS"]["sslmode"], valid_mode)

    def test_postgresql_requires_password_in_production(self):
        """En producción, rechaza contraseñas de base de datos vacías."""
        with patch.dict("os.environ", {
            "DB_ENGINE": "postgresql",
            "DB_PASSWORD": "",
            "DB_SSLMODE": "require",
        }):
            with self.assertRaises(ImproperlyConfigured):
                build_database_config(self.base_dir, debug=False)

    def test_unsupported_engine_raises_error(self):
        """Motores distintos de sqlite o postgresql son rechazados."""
        with patch.dict("os.environ", {"DB_ENGINE": "oracle"}):
            with self.assertRaises(ImproperlyConfigured):
                build_database_config(self.base_dir, debug=True)
