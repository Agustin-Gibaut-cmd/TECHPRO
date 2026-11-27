"""Smoke tests de la API TECHPRO contra un servidor en ejecución.

Requiere que el backend esté levantado y que existan los usuarios de prueba
(por ejemplo, generados mediante ``python manage.py seed_test_users``).
"""

from __future__ import annotations

import http.cookiejar
import json
import os
import unittest
import urllib.error
import urllib.request
from typing import Any

DEFAULT_API_URL = "http://127.0.0.1:8000"
DEFAULT_ADMIN_EMAIL = "admin@techpro.local"
DEFAULT_TEST_PASSWORD = "TechproTest!2026"
DEFAULT_READ_ONLY_EMAIL = "consulta@techpro.local"

REPAIR_SMOKE_PAYLOAD: dict[str, Any] = {
    "customer_name": "Cliente API",
    "customer_phone": "+54 11 1234-5678",
    "device_type": "Notebook",
    "device_model": "API Test",
    "serial_number": "api-001",
    "issue_description": "Prueba de humo de la API.",
    "status": "received",
}


class SmokeApiClient:
    """Cliente HTTP ligero con manejo de cookies y token CSRF para smoke tests."""

    def __init__(self, base_url: str, timeout: int = 15) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar)
        )

    def send(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        use_csrf: bool = False,
        expected_status: int = 200,
    ) -> Any:
        """Envía una petición HTTP, valida el código de estado y devuelve el JSON."""
        url = f"{self.base_url}{path}"
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(url, data=body, method=method)
        request.add_header("Accept", "application/json")

        if body is not None:
            request.add_header("Content-Type", "application/json")
        if use_csrf:
            request.add_header("X-CSRFToken", self.fetch_csrf_token())

        status_code, raw_body = self._execute_request(request)
        if status_code != expected_status:
            decoded = raw_body.decode("utf-8", errors="replace")
            raise AssertionError(
                f"{method} {path} -> esperado {expected_status}, "
                f"obtenido {status_code}: {decoded}"
            )
        return json.loads(raw_body.decode("utf-8")) if raw_body else None

    def fetch_csrf_token(self) -> str:
        """Obtiene el token CSRF vigente desde el endpoint de autenticación."""
        data = self.send("GET", "/api/auth/csrf/", expected_status=200)
        return str(data["csrfToken"])

    def login(
        self,
        email: str = DEFAULT_ADMIN_EMAIL,
        password: str = DEFAULT_TEST_PASSWORD,
    ) -> dict[str, Any]:
        """Inicia sesión en la API y devuelve los datos del usuario autenticado."""
        data = self.send(
            "POST",
            "/api/auth/login/",
            {"email": email, "password": password},
            use_csrf=True,
            expected_status=200,
        )
        return dict(data["user"])

    def _execute_request(self, request: urllib.request.Request) -> tuple[int, bytes]:
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                return int(response.status), response.read()
        except urllib.error.HTTPError as error:
            try:
                return int(error.code), error.read()
            finally:
                error.close()


class ApiSmokeTests(unittest.TestCase):
    """Valida salud, sesión, permisos por rol y CRUD principal de TECHPRO."""

    api_url: str
    admin_email: str
    password: str
    read_only_email: str
    client: SmokeApiClient

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.api_url = os.getenv("TECHPRO_API_URL", DEFAULT_API_URL)
        cls.admin_email = os.getenv("TECHPRO_TEST_EMAIL", DEFAULT_ADMIN_EMAIL)
        cls.password = os.getenv("TECHPRO_TEST_PASSWORD", DEFAULT_TEST_PASSWORD)
        cls.read_only_email = os.getenv(
            "TECHPRO_READ_ONLY_EMAIL", DEFAULT_READ_ONLY_EMAIL
        )

    def setUp(self) -> None:
        # Arrange
        self.client = SmokeApiClient(base_url=self.api_url)

    def test_health_check_is_public(self) -> None:
        """Verifica que el health check responda OK sin autenticación."""
        # Act
        data = self.client.send("GET", "/api/health/", expected_status=200)

        # Assert
        self.assertEqual(data, {"status": "ok"})

    def test_protected_endpoint_requires_authentication(self) -> None:
        """Verifica que el listado de reparaciones rechace peticiones anónimas (401)."""
        # Act
        data = self.client.send("GET", "/api/repairs/", expected_status=401)

        # Assert
        self.assertIn("detail", data)

    def test_login_me_and_logout_flow(self) -> None:
        """Verifica login, consulta de perfil actual y cierre de sesión."""
        # Arrange
        logged_user = self.client.login(email=self.admin_email, password=self.password)

        # Act
        current_user = self.client.send("GET", "/api/auth/me/", expected_status=200)
        self.client.send("POST", "/api/auth/logout/", {}, use_csrf=True, expected_status=204)
        after_logout = self.client.send("GET", "/api/auth/me/", expected_status=401)

        # Assert
        self.assertEqual(logged_user["email"], self.admin_email)
        self.assertEqual(current_user["email"], self.admin_email)
        self.assertIn("detail", after_logout)

    def test_invalid_login_returns_401(self) -> None:
        """Verifica que credenciales inválidas sean rechazadas con 401."""
        # Act
        data = self.client.send(
            "POST",
            "/api/auth/login/",
            {"email": self.admin_email, "password": "clave-incorrecta"},
            use_csrf=True,
            expected_status=401,
        )

        # Assert
        self.assertIn("detail", data)

    def test_repair_crud_flow(self) -> None:
        """Verifica creación, lectura, actualización y eliminación de reparaciones."""
        # Arrange
        self.client.login(email=self.admin_email, password=self.password)
        created_id: int | None = None

        # Act
        try:
            created = self.client.send(
                "POST",
                "/api/repairs/",
                REPAIR_SMOKE_PAYLOAD,
                use_csrf=True,
                expected_status=201,
            )
            created_id = int(created["id"])
            listed = self.client.send("GET", "/api/repairs/", expected_status=200)
            updated = self.client.send(
                "PATCH",
                f"/api/repairs/{created_id}/",
                {"status": "completed"},
                use_csrf=True,
                expected_status=200,
            )
            self.client.send(
                "DELETE",
                f"/api/repairs/{created_id}/",
                use_csrf=True,
                expected_status=204,
            )
            created_id = None
        finally:
            if created_id is not None:
                self.client.send(
                    "DELETE",
                    f"/api/repairs/{created_id}/",
                    use_csrf=True,
                    expected_status=204,
                )

        # Assert
        self.assertEqual(created["serial_number"], "API-001")
        self.assertTrue(any(item["id"] == created["id"] for item in listed))
        self.assertEqual(updated["status"], "completed")

    def test_read_only_role_cannot_write(self) -> None:
        """Verifica que un usuario de solo lectura reciba 403 al intentar crear."""
        # Arrange
        self.client.login(email=self.read_only_email, password=self.password)

        # Act
        data = self.client.send(
            "POST",
            "/api/customers/",
            {"name": "Cliente bloqueado", "phone": "11223344"},
            use_csrf=True,
            expected_status=403,
        )

        # Assert
        self.assertIn("detail", data)

    def test_unsupported_method_returns_405(self) -> None:
        """Verifica que PUT sobre colección de reparaciones responda 405."""
        # Arrange
        self.client.login(email=self.admin_email, password=self.password)

        # Act
        data = self.client.send(
            "PUT",
            "/api/repairs/",
            {},
            use_csrf=True,
            expected_status=405,
        )

        # Assert
        self.assertIn("detail", data)


if __name__ == "__main__":
    unittest.main(verbosity=2)