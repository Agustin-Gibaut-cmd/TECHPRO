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
        """El endpoint /api/health/ responde 200 OK y no permite caché."""
        client = APIClient()
        response = client.get("/api/health/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"status": "ok"})
        self.assertIn("no-store", response.get("Cache-Control", ""))


class ApiNoStoreMiddlewareTests(SimpleTestCase):
    """Verifica que ApiNoStoreMiddleware aplique no-store solo en rutas de API."""

    def test_middleware_patches_cache_control_on_api_routes(self):
        """Agrega no-store a las respuestas bajo /api/."""
        middleware = ApiNoStoreMiddleware(lambda _req: HttpResponse("ok"))
        request = HttpRequest()
        request.path = "/api/repairs/"

        response = middleware(request)

        self.assertIn("no-store", response.get("Cache-Control", ""))

    def test_middleware_preserves_cache_control_on_non_api_routes(self):
        """No fuerza no-store en rutas fuera del prefijo del API."""
        middleware = ApiNoStoreMiddleware(lambda _req: HttpResponse("ok"))
        request = HttpRequest()
        request.path = "/static/styles.css"

        response = middleware(request)

        self.assertNotIn("no-store", response.get("Cache-Control", ""))


class EnvParserTests(SimpleTestCase):
    """Verifica el parseo tipado y estricto de variables de entorno."""

    def test_env_str_returns_trimmed_text_or_default(self):
        """Limpia espacios laterales y respeta el valor por defecto."""
        with patch.dict("os.environ", {"TEST_VAR": "  hola taller  "}):
            self.assertEqual(env_str("TEST_VAR"), "hola taller")
        self.assertEqual(env_str("NON_EXISTENT", default="fallback"), "fallback")

    def test_env_bool_parses_truthy_values(self):
        """Interpreta valores afirmativos estándar como True."""
        for value in ("1", "true", "True", "YES", "on"):
            with patch.dict("os.environ", {"TEST_BOOL": value}):
                self.assertTrue(env_bool("TEST_BOOL"))

    def test_env_bool_parses_falsy_values(self):
        """Interpreta valores negativos estándar como False."""
        for value in ("0", "false", "False", "NO", "off"):
            with patch.dict("os.environ", {"TEST_BOOL": value}):
                self.assertFalse(env_bool("TEST_BOOL"))

    def test_env_bool_raises_on_invalid_string(self):
        """Lanza ImproperlyConfigured ante valores booleanos inválidos."""
        with patch.dict("os.environ", {"TEST_BOOL": "talvez"}):
            with self.assertRaises(ImproperlyConfigured):
                env_bool("TEST_BOOL")

    def test_env_int_parses_valid_integers(self):
        """Convierte enteros válidos y devuelve el default si falta la variable."""
        with patch.dict("os.environ", {"TEST_INT": "  42  "}):
            self.assertEqual(env_int("TEST_INT", 0), 42)
        self.assertEqual(env_int("NON_EXISTENT_INT", 99), 99)

    def test_env_int_raises_on_invalid_number(self):
        """Lanza ImproperlyConfigured si el valor entero no es numérico."""
        with patch.dict("os.environ", {"TEST_INT": "cuarenta_y_dos"}):
            with self.assertRaises(ImproperlyConfigured):
                env_int("TEST_INT", 0)

    def test_env_list_splits_and_trims(self):
        """Separa por comas, recorta espacios y omite vacíos."""
        with patch.dict("os.environ", {"TEST_LIST": " a, b , , c "}):
            self.assertEqual(env_list("TEST_LIST"), ["a", "b", "c"])


class SecretKeysSecurityTests(SimpleTestCase):
    """Audita longitud, entropía y unicidad de DJANGO_SECRET_KEY y JWT_SIGNING_KEY."""

    def setUp(self):
        self.valid_key_1 = secrets.token_urlsafe(48)
        self.valid_key_2 = secrets.token_urlsafe(48)

    def test_load_secret_keys_succeeds_with_valid_distinct_keys(self):
        """Acepta dos claves fuertes y distintas."""
        with patch.dict(
            "os.environ",
            {
                "DJANGO_SECRET_KEY": self.valid_key_1,
                "JWT_SIGNING_KEY": self.valid_key_2,
            },
        ):
            key_1, key_2 = load_secret_keys()
            self.assertEqual(key_1, self.valid_key_1)
            self.assertEqual(key_2, self.valid_key_2)

    def test_load_secret_keys_rejects_short_django_key(self):
        """Rechaza una DJANGO_SECRET_KEY corta."""
        with patch.dict(
            "os.environ",
            {
                "DJANGO_SECRET_KEY": "corta",
                "JWT_SIGNING_KEY": self.valid_key_2,
            },
        ):
            with self.assertRaises(ImproperlyConfigured):
                load_secret_keys()

    def test_load_secret_keys_rejects_placeholder_prefix(self):
        """Rechaza claves con prefijo inseguro de plantilla."""
        with patch.dict(
            "os.environ",
            {
                "DJANGO_SECRET_KEY": f"replace-with-{self.valid_key_1}",
                "JWT_SIGNING_KEY": self.valid_key_2,
            },
        ):
            with self.assertRaises(ImproperlyConfigured):
                load_secret_keys()

    def test_load_secret_keys_rejects_identical_keys(self):
        """Exige que JWT_SIGNING_KEY sea distinta a DJANGO_SECRET_KEY."""
        with patch.dict(
            "os.environ",
            {
                "DJANGO_SECRET_KEY": self.valid_key_1,
                "JWT_SIGNING_KEY": self.valid_key_1,
            },
        ):
            with self.assertRaises(ImproperlyConfigured):
                load_secret_keys()


class ProductionSecurityAuditTests(SimpleTestCase):
    """Audita las reglas estrictas de arranque cuando DEBUG=False."""

    def setUp(self):
        self.valid_k1 = secrets.token_urlsafe(48)
        self.valid_k2 = secrets.token_urlsafe(48)

    def test_audit_passes_in_debug_development_mode(self):
        """Permite configuración local cuando ENVIRONMENT=development y DEBUG=True."""
        validate_production_settings(
            environment="development",
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

    def test_audit_rejects_debug_true_in_production_environment(self):
        """Bloquea ENVIRONMENT=production con DEBUG=True."""
        with self.assertRaises(ImproperlyConfigured):
            validate_production_settings(
                environment="production",
                debug=True,
                secret_key=self.valid_k1,
                jwt_key=self.valid_k2,
                allowed_hosts=["taller.example.com"],
                cors_origins=["https://taller.example.com"],
                csrf_origins=["https://taller.example.com"],
                ssl_redirect=True,
                hsts_seconds=31_536_000,
                hsts_preload=False,
                hsts_subdomains=False,
            )

    def test_audit_rejects_dev_keys_in_production(self):
        """Rechaza claves con prefijo dev- cuando DEBUG=False."""
        with self.assertRaises(ImproperlyConfigured):
            validate_production_settings(
                environment="production",
                debug=False,
                secret_key=f"dev-{self.valid_k1}",
                jwt_key=self.valid_k2,
                allowed_hosts=["taller.example.com"],
                cors_origins=["https://taller.example.com"],
                csrf_origins=["https://taller.example.com"],
                ssl_redirect=True,
                hsts_seconds=31_536_000,
                hsts_preload=False,
                hsts_subdomains=False,
            )

    def test_audit_rejects_wildcard_allowed_hosts(self):
        """Rechaza comodín '*' en DJANGO_ALLOWED_HOSTS cuando DEBUG=False."""
        with self.assertRaises(ImproperlyConfigured):
            validate_production_settings(
                environment="production",
                debug=False,
                secret_key=self.valid_k1,
                jwt_key=self.valid_k2,
                allowed_hosts=["*"],
                cors_origins=["https://taller.example.com"],
                csrf_origins=["https://taller.example.com"],
                ssl_redirect=True,
                hsts_seconds=31_536_000,
                hsts_preload=False,
                hsts_subdomains=False,
            )

    def test_audit_rejects_http_and_local_origins(self):
        """Rechaza orígenes HTTP o locales/privados cuando DEBUG=False."""
        with self.assertRaises(ImproperlyConfigured):
            validate_production_settings(
                environment="production",
                debug=False,
                secret_key=self.valid_k1,
                jwt_key=self.valid_k2,
                allowed_hosts=["taller.example.com"],
                cors_origins=["http://localhost:4200"],
                csrf_origins=["https://taller.example.com"],
                ssl_redirect=True,
                hsts_seconds=31_536_000,
                hsts_preload=False,
                hsts_subdomains=False,
            )

    def test_audit_rejects_disabled_ssl_redirect(self):
        """Exige SECURE_SSL_REDIRECT=True cuando DEBUG=False."""
        with self.assertRaises(ImproperlyConfigured):
            validate_production_settings(
                environment="production",
                debug=False,
                secret_key=self.valid_k1,
                jwt_key=self.valid_k2,
                allowed_hosts=["taller.example.com"],
                cors_origins=["https://taller.example.com"],
                csrf_origins=["https://taller.example.com"],
                ssl_redirect=False,
                hsts_seconds=31_536_000,
                hsts_preload=False,
                hsts_subdomains=False,
            )