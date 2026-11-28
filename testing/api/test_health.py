"""Smoke tests de salud y acceso anónimo."""

from .base import SmokeApiTestCase


class HealthSmokeTests(SmokeApiTestCase):
    def test_health_check_is_public(self) -> None:
        data = self.client.send("GET", "/api/health/", expected_status=200)
        self.assertEqual(data, {"status": "ok"})

    def test_protected_endpoint_requires_authentication(self) -> None:
        data = self.client.send("GET", "/api/repairs/", expected_status=401)
        self.assertIn("detail", data)
