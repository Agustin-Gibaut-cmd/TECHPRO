"""Smoke tests de autenticación y sesión."""

from .base import SmokeApiTestCase
from .constants import REPAIR_SMOKE_PAYLOAD


class AuthSmokeTests(SmokeApiTestCase):
    def test_login_me_and_logout_flow(self) -> None:
        logged_user = self.client.login(email=self.admin_email, password=self.password)
        current_user = self.client.send("GET", "/api/auth/me/", expected_status=200)
        self.client.send("POST", "/api/auth/logout/", {}, use_csrf=True, expected_status=204)
        after_logout = self.client.send("GET", "/api/auth/me/", expected_status=401)

        self.assertEqual(logged_user["email"], self.admin_email)
        self.assertEqual(current_user["email"], self.admin_email)
        self.assertIn("detail", after_logout)

    def test_invalid_login_returns_401(self) -> None:
        data = self.client.send(
            "POST",
            "/api/auth/login/",
            {"email": self.admin_email, "password": "clave-incorrecta"},
            use_csrf=True,
            expected_status=401,
        )
        self.assertIn("detail", data)
