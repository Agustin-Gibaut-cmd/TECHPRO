"""Smoke tests de permisos por rol."""

from .base import SmokeApiTestCase


class RoleSmokeTests(SmokeApiTestCase):
    def test_read_only_role_cannot_write(self) -> None:
        self.client.login(email=self.read_only_email, password=self.password)
        data = self.client.send(
            "POST",
            "/api/customers/",
            {"name": "Cliente bloqueado", "phone": "11223344"},
            use_csrf=True,
            expected_status=403,
        )
        self.assertIn("detail", data)
