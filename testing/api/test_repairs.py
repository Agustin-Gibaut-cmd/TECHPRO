"""Smoke tests de CRUD de reparaciones."""

from .base import SmokeApiTestCase
from .constants import REPAIR_SMOKE_PAYLOAD


class RepairSmokeTests(SmokeApiTestCase):
    def test_repair_crud_flow(self) -> None:
        self.client.login(email=self.admin_email, password=self.password)
        created_id: int | None = None

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

        self.assertEqual(created["serial_number"], "API-001")
        self.assertTrue(any(item["id"] == created["id"] for item in listed))
        self.assertEqual(updated["status"], "completed")

    def test_unsupported_method_returns_405(self) -> None:
        self.client.login(email=self.admin_email, password=self.password)
        data = self.client.send(
            "PUT",
            "/api/repairs/",
            {},
            use_csrf=True,
            expected_status=405,
        )
        self.assertIn("detail", data)
