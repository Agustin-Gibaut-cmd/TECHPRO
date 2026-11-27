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
        # Arrange
        environment = {"DB_ENGINE": "sqlite", "SQLITE_DB_NAME": "test.sqlite3"}

        # Act
        with patch.dict("os.environ", environment):
            db_config = build_database_config(self.base_dir, debug=True)

        # Assert
        self.assertEqual(db_config["ENGINE"], "django.db.backends.sqlite3")
        self.assertEqual(db_config["NAME"], self.base_dir / "test.sqlite3")

    def test_sqlite_rejected_in_production(self):
        # Arrange
        environment = {"DB_ENGINE": "sqlite"}

        # Act
        with patch.dict("os.environ", environment):
            with self.assertRaises(ImproperlyConfigured) as ctx:
                build_database_config(self.base_dir, debug=False)

        # Assert
        self.assertIn("PostgreSQL", str(ctx.exception))

    def test_postgresql_config_generation_in_development(self):
        # Arrange
        environment = {
            "DB_ENGINE": "postgresql",
            "DB_NAME": "test_db",
            "DB_USER": "test_user",
            "DB_PASSWORD": "secret_password",
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "DB_SSLMODE": "prefer",
        }

        # Act
        with patch.dict("os.environ", environment):
            db_config = build_database_config(self.base_dir, debug=True)

        # Assert
        self.assertEqual(db_config["ENGINE"], "django.db.backends.postgresql")
        self.assertEqual(db_config["NAME"], "test_db")
        self.assertEqual(db_config["USER"], "test_user")
        self.assertEqual(db_config["PASSWORD"], "secret_password")
        self.assertEqual(db_config["OPTIONS"]["sslmode"], "prefer")

    def test_postgresql_requires_strong_sslmode_in_production(self):
        # Arrange
        environment = {
            "DB_ENGINE": "postgresql",
            "DB_PASSWORD": "secret_password",
            "DB_SSLMODE": "prefer",
        }

        # Act
        with patch.dict("os.environ", environment):
            with self.assertRaises(ImproperlyConfigured) as ctx:
                build_database_config(self.base_dir, debug=False)

        # Assert
        self.assertIn("TLS", str(ctx.exception))

    def test_postgresql_accepts_valid_tls_sslmode_in_production(self):
        # Arrange
        valid_modes = ("require", "verify-ca", "verify-full")

        # Act
        configs = []
        for valid_mode in valid_modes:
            with patch.dict(
                "os.environ",
                {
                    "DB_ENGINE": "postgresql",
                    "DB_PASSWORD": "secret_password",
                    "DB_SSLMODE": valid_mode,
                },
            ):
                configs.append(build_database_config(self.base_dir, debug=False))

        # Assert
        for valid_mode, db_config in zip(valid_modes, configs):
            self.assertEqual(db_config["OPTIONS"]["sslmode"], valid_mode)

    def test_postgresql_requires_password_in_production(self):
        # Arrange
        environment = {
            "DB_ENGINE": "postgresql",
            "DB_PASSWORD": "",
            "DB_SSLMODE": "require",
        }

        # Act
        with patch.dict("os.environ", environment):
            with self.assertRaises(ImproperlyConfigured) as ctx:
                build_database_config(self.base_dir, debug=False)

        # Assert
        self.assertIn("DB_PASSWORD", str(ctx.exception))

    def test_unsupported_engine_raises_error(self):
        # Arrange
        environment = {"DB_ENGINE": "oracle"}

        # Act
        with patch.dict("os.environ", environment):
            with self.assertRaises(ImproperlyConfigured) as ctx:
                build_database_config(self.base_dir, debug=True)

        # Assert
        self.assertIn("DB_ENGINE", str(ctx.exception))
