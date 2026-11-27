"""Pruebas unitarias y de integración para configuración, entorno y middleware."""

import secrets
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest, HttpResponse
from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.test import APIClient

from config.env import (
    env_bool,
    env_int,
    env_list,
    env_str,
    load_secret_keys,
    validate_production_settings,
)
from config.middleware import ApiNoStoreMiddleware


class HealthCheckApiTests(SimpleTestCase):
    """Verifica la disponibilidad del endpoint público de salud."""

    def test_health_check_returns_ok_status(self):
        # Arrange
        client = APIClient()

        # Act
        response = client.get("/api/health/")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"status": "ok"})
        self.assertIn("no-store", response.get("Cache-Control", ""))


class ApiNoStoreMiddlewareTests(SimpleTestCase):
    """Verifica que ApiNoStoreMiddleware aplique no-store solo en rutas de API."""

    def test_middleware_patches_cache_control_on_api_routes(self):
        # Arrange
        middleware = ApiNoStoreMiddleware(lambda _req: HttpResponse("ok"))
        request = HttpRequest()
        request.path = "/api/repairs/"

        # Act
        response = middleware(request)

        # Assert
        self.assertIn("no-store", response.get("Cache-Control", ""))

    def test_middleware_preserves_cache_control_on_non_api_routes(self):
        # Arrange
        middleware = ApiNoStoreMiddleware(lambda _req: HttpResponse("ok"))
        request = HttpRequest()
        request.path = "/static/styles.css"

        # Act
        response = middleware(request)

        # Assert
        self.assertNotIn("no-store", response.get("Cache-Control", ""))


class EnvParserTests(SimpleTestCase):
    """Verifica el parseo tipado y estricto de variables de entorno."""

    def test_env_str_returns_trimmed_text_or_default(self):
        # Arrange
        environment = {"TEST_VAR": "  hola taller  "}

        # Act
        with patch.dict("os.environ", environment):
            value = env_str("TEST_VAR")
        fallback = env_str("NON_EXISTENT", default="fallback")

        # Assert
        self.assertEqual(value, "hola taller")
        self.assertEqual(fallback, "fallback")

    def test_env_bool_parses_truthy_values(self):
        # Arrange
        values = ("1", "true", "True", "YES", "on")

        # Act
        results = []
        for value in values:
            with patch.dict("os.environ", {"TEST_BOOL": value}):
                results.append(env_bool("TEST_BOOL"))

        # Assert
        self.assertTrue(all(results))

    def test_env_bool_parses_falsy_values(self):
        # Arrange
        values = ("0", "false", "False", "NO", "off")

        # Act
        results = []
        for value in values:
            with patch.dict("os.environ", {"TEST_BOOL": value}):
                results.append(env_bool("TEST_BOOL"))

        # Assert
        self.assertFalse(any(results))

    def test_env_bool_raises_on_invalid_string(self):
        # Arrange
        environment = {"TEST_BOOL": "talvez"}

        # Act
        with patch.dict("os.environ", environment):
            with self.assertRaises(ImproperlyConfigured) as ctx:
                env_bool("TEST_BOOL")

        # Assert
        self.assertIn("booleano", str(ctx.exception))

    def test_env_int_parses_valid_integers(self):
        # Arrange
        environment = {"TEST_INT": "  42  "}

        # Act
        with patch.dict("os.environ", environment):
            value = env_int("TEST_INT", 0)
        fallback = env_int("NON_EXISTENT_INT", 99)

        # Assert
        self.assertEqual(value, 42)
        self.assertEqual(fallback, 99)

    def test_env_int_raises_on_invalid_number(self):
        # Arrange
        environment = {"TEST_INT": "cuarenta_y_dos"}

        # Act
        with patch.dict("os.environ", environment):
            with self.assertRaises(ImproperlyConfigured) as ctx:
                env_int("TEST_INT", 0)

        # Assert
        self.assertIn("entero", str(ctx.exception))

    def test_env_list_splits_and_trims(self):
        # Arrange
        environment = {"TEST_LIST": " a, b , , c "}

        # Act
        with patch.dict("os.environ", environment):
            values = env_list("TEST_LIST")

        # Assert
        self.assertEqual(values, ["a", "b", "c"])


class SecretKeysSecurityTests(SimpleTestCase):
    """Audita longitud, entropía y unicidad de DJANGO_SECRET_KEY y JWT_SIGNING_KEY."""

    def setUp(self):
        self.valid_key_1 = secrets.token_urlsafe(48)
        self.valid_key_2 = secrets.token_urlsafe(48)

    def test_load_secret_keys_succeeds_with_valid_distinct_keys(self):
        # Arrange
        environment = {
            "DJANGO_SECRET_KEY": self.valid_key_1,
            "JWT_SIGNING_KEY": self.valid_key_2,
        }

        # Act
        with patch.dict("os.environ", environment):
            key_1, key_2 = load_secret_keys()

        # Assert
        self.assertEqual(key_1, self.valid_key_1)
        self.assertEqual(key_2, self.valid_key_2)

    def test_load_secret_keys_rejects_short_django_key(self):
        # Arrange
        environment = {
            "DJANGO_SECRET_KEY": "corta",
            "JWT_SIGNING_KEY": self.valid_key_2,
        }

        # Act
        with patch.dict("os.environ", environment):
            with self.assertRaises(ImproperlyConfigured) as ctx:
                load_secret_keys()

        # Assert
        self.assertIn("DJANGO_SECRET_KEY", str(ctx.exception))

    def test_load_secret_keys_rejects_placeholder_prefix(self):
        # Arrange
        environment = {
            "DJANGO_SECRET_KEY": f"replace-with-{self.valid_key_1}",
            "JWT_SIGNING_KEY": self.valid_key_2,
        }

        # Act
        with patch.dict("os.environ", environment):
            with self.assertRaises(ImproperlyConfigured) as ctx:
                load_secret_keys()

        # Assert
        self.assertIn("DJANGO_SECRET_KEY", str(ctx.exception))

    def test_load_secret_keys_rejects_identical_keys(self):
        # Arrange
        environment = {
            "DJANGO_SECRET_KEY": self.valid_key_1,
            "JWT_SIGNING_KEY": self.valid_key_1,
        }

        # Act
        with patch.dict("os.environ", environment):
            with self.assertRaises(ImproperlyConfigured) as ctx:
                load_secret_keys()

        # Assert
        self.assertIn("distinto", str(ctx.exception))


class ProductionSecurityAuditTests(SimpleTestCase):
    """Audita las reglas estrictas de arranque cuando DEBUG=False."""

    def setUp(self):
        self.valid_k1 = secrets.token_urlsafe(48)
        self.valid_k2 = secrets.token_urlsafe(48)

    def _production_kwargs(self, **overrides) -> dict:
        kwargs = {
            "environment": "production",
            "debug": False,
            "secret_key": self.valid_k1,
            "jwt_key": self.valid_k2,
            "allowed_hosts": ["taller.example.com"],
            "cors_origins": ["https://taller.example.com"],
            "csrf_origins": ["https://taller.example.com"],
            "ssl_redirect": True,
            "hsts_seconds": 31_536_000,
            "hsts_preload": False,
            "hsts_subdomains": False,
        }
        kwargs.update(overrides)
        return kwargs

    def test_audit_passes_in_debug_development_mode(self):
        # Arrange
        kwargs = {
            "environment": "development",
            "debug": True,
            "secret_key": "dev-key",
            "jwt_key": "dev-key-2",
            "allowed_hosts": [],
            "cors_origins": [],
            "csrf_origins": [],
            "ssl_redirect": False,
            "hsts_seconds": 0,
            "hsts_preload": False,
            "hsts_subdomains": False,
        }

        # Act
        result = validate_production_settings(**kwargs)

        # Assert
        self.assertIsNone(result)

    def test_audit_rejects_debug_true_in_production_environment(self):
        # Arrange
        kwargs = self._production_kwargs(debug=True)

        # Act
        with self.assertRaises(ImproperlyConfigured) as ctx:
            validate_production_settings(**kwargs)

        # Assert
        self.assertIn("DEBUG", str(ctx.exception))

    def test_audit_rejects_dev_keys_in_production(self):
        # Arrange
        kwargs = self._production_kwargs(secret_key=f"dev-{self.valid_k1}")

        # Act
        with self.assertRaises(ImproperlyConfigured) as ctx:
            validate_production_settings(**kwargs)

        # Assert
        self.assertIn("secretos", str(ctx.exception))

    def test_audit_rejects_wildcard_allowed_hosts(self):
        # Arrange
        kwargs = self._production_kwargs(allowed_hosts=["*"])

        # Act
        with self.assertRaises(ImproperlyConfigured) as ctx:
            validate_production_settings(**kwargs)

        # Assert
        self.assertIn("DJANGO_ALLOWED_HOSTS", str(ctx.exception))

    def test_audit_rejects_http_and_local_origins(self):
        # Arrange
        kwargs = self._production_kwargs(
            cors_origins=["http://localhost:4200"]
        )

        # Act
        with self.assertRaises(ImproperlyConfigured) as ctx:
            validate_production_settings(**kwargs)

        # Assert
        self.assertIn("local", str(ctx.exception).lower())

    def test_audit_rejects_disabled_ssl_redirect(self):
        # Arrange
        kwargs = self._production_kwargs(ssl_redirect=False)

        # Act
        with self.assertRaises(ImproperlyConfigured) as ctx:
            validate_production_settings(**kwargs)

        # Assert
        self.assertIn("SECURE_SSL_REDIRECT", str(ctx.exception))
