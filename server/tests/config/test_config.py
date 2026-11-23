"""Pruebas unitarias para utilidades de configuración, entorno y middleware."""

from pathlib import Path
from unittest.mock import MagicMock, patch

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
    """Verifica la operatividad del endpoint público de diagnóstico del sistema."""

    def test_health_check_returns_ok_status(self):
        """El endpoint /api/health/ responde 200 OK con estado saludable."""
        client = APIClient()
        response = client.get("/api/health/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"status": "ok"})
        self.assertEqual(response["Cache-Control"], "no-store")


class ApiNoStoreMiddlewareTests(SimpleTestCase):
    """Verifica que el middleware aplique Cache-Control exclusivamente en rutas de API."""

    def test_middleware_patches_cache_control_on_api_routes(self):
        """Las rutas que inician con /api/ deben recibir Cache-Control: no-store."""
        middleware = ApiNoStoreMiddleware(lambda req: HttpResponse("ok"))
        request = HttpRequest()
        request.path = "/api/repairs/"

        response = middleware(request)

        self.assertIn("no-store", response.get("Cache-Control", ""))

    def test_middleware_preserves_cache_control_on_non_api_routes(self):
        """Las rutas que no pertenecen al API no deben ser forzadas con no-store."""
        middleware = ApiNoStoreMiddleware(lambda req: HttpResponse("ok"))
        request = HttpRequest()
        request.path = "/static/styles.css"

        response = middleware(request)

        self.assertNotIn("no-store", response.get("Cache-Control", ""))


class EnvParserTests(SimpleTestCase):
    """Verifica el parseo estricto de variables de entorno y sus validaciones."""

    def test_env_str_returns_trimmed_text_or_default(self):
        """env_str elimina espacios periféricos y devuelve el valor predeterminado si no existe."""
        with patch.dict("os.environ", {"TEST_VAR": "  hola taller  "}):
            self.assertEqual(env_str("TEST_VAR"), "hola taller")
        self.assertEqual(env_str("NON_EXISTENT", default="fallback"), "fallback")

    def test_env_bool_parses_truthy_values(self):
        """Valores 1, true, yes y on se interpretan como True."""
        for val in ("1", "true", "True", "YES", "on"):
            with patch.dict("os.environ", {"TEST_BOOL": val}):
                self.assertTrue(env_bool("TEST_BOOL"))

    def test_env_bool_parses_falsy_values(self):
        """Valores 0, false, no y off se interpretan como False."""
        for val in ("0", "false", "False", "NO", "off"):
            with patch.dict("os.environ", {"TEST_BOOL": val}):
                self.assertFalse(env_bool("TEST_BOOL"))

    def test_env_bool_raises_on_invalid_string(self):
        """Valores no booleanos lanzan ImproperlyConfigured."""
        with patch.dict("os.environ", {"TEST_BOOL": "talvez"}):
            with self.assertRaises(ImproperlyConfigured):
                env_bool("TEST_BOOL")

    def test_env_int_parses_valid_integers(self):
        """Convierte enteros correctamente y respeta defaults."""
        with patch.dict("os.environ", {"TEST_INT": "  42  "}):
            self.assertEqual(env_int("TEST_INT", 0), 42)
        self.assertEqual(env_int("NON_EXISTENT_INT", 99), 99)

    def test_env_int_raises_on_invalid_number(self):
        """Cadenas no numéricas lanzan ImproperlyConfigured."""
        with patch.dict("os.environ", {"TEST_INT": "cuarenta_y_dos"}):
            with self.assertRaises(ImproperlyConfigured):
                env_int("TEST_INT", 0)

    def test_env_list_splits_and_trims(self):
        """Divide por comas ignorando elementos vacíos."""
        with patch.dict("os.environ", {"TEST_LIST": " a, b , , c "}):
            self.assertEqual(env_list("TEST_LIST"), ["a", "b", "c"])


class SecretKeysSecurityTests(SimpleTestCase):
    """Verifica las reglas de seguridad aplicadas a las claves criptográficas."""

    VALID_KEY_1 = "a" * 50
    VALID_KEY_2 = "b" * 50

    def test_load_secret_keys_succeeds_with_valid_distinct_keys(self):
        """Acepta claves con 50 o más caracteres si son distintas."""
        with patch.dict("os.environ", {
            "DJANGO_SECRET_KEY": self.VALID_KEY_1,
            "JWT_SIGNING_KEY": self.VALID_KEY_2,
        }):
            k1, k2 = load_secret_keys()
            self.assertEqual(k1, self.VALID_KEY_1)
            self.assertEqual(k2, self.VALID_KEY_2)

    def test_load_secret_keys_rejects_short_django_key(self):
        """Rechaza DJANGO_SECRET_KEY con longitud menor a 50 caracteres."""
        with patch.dict("os.environ", {
            "DJANGO_SECRET_KEY": "corta",
            "JWT_SIGNING_KEY": self.VALID_KEY_2,
        }):
            with self.assertRaises(ImproperlyConfigured):
                load_secret_keys()

    def test_load_secret_keys_rejects_placeholder_prefix(self):
        """Rechaza claves que comiencen con el prefijo de plantilla replace-with-."""
        with patch.dict("os.environ", {
            "DJANGO_SECRET_KEY": "replace-with-a-random-secret-that-is-at-least-50-characters",
            "JWT_SIGNING_KEY": self.VALID_KEY_2,
        }):
            with self.assertRaises(ImproperlyConfigured):
                load_secret_keys()

    def test_load_secret_keys_rejects_identical_keys(self):
        """Rechaza que JWT_SIGNING_KEY sea idéntica a DJANGO_SECRET_KEY."""
        with patch.dict("os.environ", {
            "DJANGO_SECRET_KEY": self.VALID_KEY_1,
            "JWT_SIGNING_KEY": self.VALID_KEY_1,
        }):
            with self.assertRaises(ImproperlyConfigured):
                load_secret_keys()


class ProductionSecurityAuditTests(SimpleTestCase):
    """Audita las restricciones de seguridad obligatorias cuando DEBUG=False."""

    VALID_K1 = "prod-secret-key-1-" + "x" * 40
    VALID_K2 = "prod-secret-key-2-" + "y" * 40

    def test_audit_passes_in_debug_mode_without_restrictions(self):
        """En modo depuración (DEBUG=True), la auditoría no lanza excepciones."""
        validate_production_settings(
            debug=True,
            secret_key="dev-key",
            jwt_key="dev-key-2",
            allowed_hosts=[],
            cors_origins=[],
            csrf_origins=[],
            ssl_redirect=False,
            hsts_seconds=0,
            hsts_preload=False,
            hsts_subdomains=False,
        )

    def test_audit_rejects_dev_keys_in_production(self):
        """Rechaza claves con prefijo dev- en entorno de producción."""
        with self.assertRaises(ImproperlyConfigured):
            validate_production_settings(
                debug=False,
                secret_key="dev-key-that-is-long-enough-for-validation-50-chars-here",
                jwt_key=self.VALID_K2,
                allowed_hosts=["taller.example.com"],
                cors_origins=["https://taller.example.com"],
                csrf_origins=["https://taller.example.com"],
                ssl_redirect=True,
                hsts_seconds=31536000,
                hsts_preload=False,
                hsts_subdomains=False,
            )

    def test_audit_rejects_wildcard_allowed_hosts(self):
        """Rechaza ALLOWED_HOSTS con comodín '*' en producción."""
        with self.assertRaises(ImproperlyConfigured):
            validate_production_settings(
                debug=False,
                secret_key=self.VALID_K1,
                jwt_key=self.VALID_K2,
                allowed_hosts=["*"],
                cors_origins=["https://taller.example.com"],
                csrf_origins=["https://taller.example.com"],
                ssl_redirect=True,
                hsts_seconds=31536000,
                hsts_preload=False,
                hsts_subdomains=False,
            )

    def test_audit_rejects_http_and_local_origins(self):
        """Rechaza orígenes HTTP no seguros o que apunten a localhost en producción."""
        with self.assertRaises(ImproperlyConfigured):
            validate_production_settings(
                debug=False,
                secret_key=self.VALID_K1,
                jwt_key=self.VALID_K2,
                allowed_hosts=["taller.example.com"],
                cors_origins=["http://localhost:4200"],
                csrf_origins=["https://taller.example.com"],
                ssl_redirect=True,
                hsts_seconds=31536000,
                hsts_preload=False,
                hsts_subdomains=False,
            )

    def test_audit_rejects_disabled_ssl_redirect(self):
        """Rechaza SECURE_SSL_REDIRECT=False en producción."""
        with self.assertRaises(ImproperlyConfigured):
            validate_production_settings(
                debug=False,
                secret_key=self.VALID_K1,
                jwt_key=self.VALID_K2,
                allowed_hosts=["taller.example.com"],
                cors_origins=["https://taller.example.com"],
                csrf_origins=["https://taller.example.com"],
                ssl_redirect=False,
                hsts_seconds=31536000,
                hsts_preload=False,
                hsts_subdomains=False,
            )
