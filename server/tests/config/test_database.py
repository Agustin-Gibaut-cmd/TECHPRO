"""Pruebas unitarias para el constructor y validador de bases de datos."""

from pathlib import Path
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from config.database import build_database_config


class DatabaseConfigTests(SimpleTestCase):
    """Valida la generación de configuración para SQLite y PostgreSQL."""

    def setUp(self):
        self.base_dir = Path("/mock/base/dir")

    def test_sqlite_config_generation_in_debug_mode(self):
        """Genera configuración SQLite válida cuando DEBUG=True."""
        with patch.dict(
            "os.environ",
            {"DB_ENGINE": "sqlite", "SQLITE_DB_NAME": "test.sqlite3"},
        ):
            db_config = build_database_config(self.base_dir, debug=True)
            self.assertEqual(db_config["ENGINE"], "django.db.backends.sqlite3")
            self.assertEqual(db_config["NAME"], self.base_dir / "test.sqlite3")

    def test_sqlite_rejected_in_production(self):
        """Rechaza SQLite cuando DEBUG=False."""
        with patch.dict("os.environ", {"DB_ENGINE": "sqlite"}):
            with self.assertRaises(ImproperlyConfigured):
                build_database_config(self.base_dir, debug=False)

    def test_postgresql_config_generation_in_development(self):
        """Construye configuración PostgreSQL estándar en modo desarrollo."""
        with patch.dict(
            "os.environ",
            {
                "DB_ENGINE": "postgresql",
                "DB_NAME": "test_db",
                "DB_USER": "test_user",
                "DB_PASSWORD": "secret_password",
                "DB_HOST": "localhost",
                "DB_PORT": "5432",
                "DB_SSLMODE": "prefer",
            },
        ):
            db_config = build_database_config(self.base_dir, debug=True)
            self.assertEqual(db_config["ENGINE"], "django.db.backends.postgresql")
            self.assertEqual(db_config["NAME"], "test_db")
            self.assertEqual(db_config["USER"], "test_user")
            self.assertEqual(db_config["PASSWORD"], "secret_password")
            self.assertEqual(db_config["OPTIONS"]["sslmode"], "prefer")

    def test_postgresql_requires_strong_sslmode_in_production(self):
        """Rechaza sslmode débil ('prefer' o 'disable') cuando DEBUG=False."""
        with patch.dict(
            "os.environ",
            {
                "DB_ENGINE": "postgresql",
                "DB_PASSWORD": "secret_password",
                "DB_SSLMODE": "prefer",
            },
        ):
            with self.assertRaises(ImproperlyConfigured):
                build_database_config(self.base_dir, debug=False)

    def test_postgresql_accepts_valid_tls_sslmode_in_production(self):
        """Acepta sslmode TLS válido cuando DEBUG=False."""
        for valid_mode in ("require", "verify-ca", "verify-full"):
            with patch.dict(
                "os.environ",
                {
                    "DB_ENGINE": "postgresql",
                    "DB_PASSWORD": "secret_password",
                    "DB_SSLMODE": valid_mode,
                },
            ):
                db_config = build_database_config(self.base_dir, debug=False)
                self.assertEqual(db_config["OPTIONS"]["sslmode"], valid_mode)

    def test_postgresql_requires_password_in_production(self):
        """Exige DB_PASSWORD no vacía cuando DEBUG=False."""
        with patch.dict(
            "os.environ",
            {
                "DB_ENGINE": "postgresql",
                "DB_PASSWORD": "",
                "DB_SSLMODE": "require",
            },
        ):
            with self.assertRaises(ImproperlyConfigured):
                build_database_config(self.base_dir, debug=False)

    def test_unsupported_engine_raises_error(self):
        """Lanza ImproperlyConfigured para motores distintos a sqlite o postgresql."""
        with patch.dict("os.environ", {"DB_ENGINE": "oracle"}):
            with self.assertRaises(ImproperlyConfigured):
                build_database_config(self.base_dir, debug=True)