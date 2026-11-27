"""Pruebas de integración para el módulo de órdenes de reparación."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from repairs.models import Repair
from tests.support import create_user, repair_payload


class RepairApiTests(APITestCase):
    """Valida CRUD, normalización, validaciones y aislamiento multitenant."""

    def setUp(self):
        # Arrange
        self.user = create_user()
        self.client.force_authenticate(self.user)
        self.payload = repair_payload()
        self.list_url = reverse("repair-list-create")

    def _detail_url(self, repair_id: int) -> str:
        return reverse("repair-update", args=[repair_id])

    def test_authenticated_user_can_create_list_and_retrieve_repair(self):
        # Arrange
        payload = self.payload

        # Act
        create_response = self.client.post(self.list_url, payload, format="json")
        list_response = self.client.get(self.list_url)
        detail_response = self.client.get(self._detail_url(create_response.data["id"]))

        # Assert
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_response.data["customer_name"], "Ana Pérez")
        self.assertEqual(create_response.data["serial_number"], "SN-123456")
        self.assertEqual(create_response.data["status"], "diagnosing")
        self.assertEqual(Repair.objects.get().created_by, self.user)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(list_response.data[0]["id"], create_response.data["id"])
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)

    def test_create_repair_validates_required_fields(self):
        # Arrange
        incomplete_payload = {
            "device_model": "ThinkPad T14",
            "issue_description": "Sin datos de cliente",
        }

        # Act
        response = self.client.post(self.list_url, incomplete_payload, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("customer_name", response.data)
        self.assertIn("customer_phone", response.data)
        self.assertIn("device_type", response.data)

    def test_create_repair_validates_max_description_length(self):
        # Arrange
        payload = repair_payload(issue_description="x" * 2001)

        # Act
        response = self.client.post(self.list_url, payload, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("issue_description", response.data)

    def test_create_repair_validates_phone_and_serial_format(self):
        # Arrange
        invalid_phone = repair_payload(customer_phone="abc-telefono!")
        invalid_serial = repair_payload(serial_number="SN$INVALID@123")

        # Act
        phone_response = self.client.post(self.list_url, invalid_phone, format="json")
        serial_response = self.client.post(self.list_url, invalid_serial, format="json")

        # Assert
        self.assertEqual(phone_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("customer_phone", phone_response.data)
        self.assertEqual(serial_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("serial_number", serial_response.data)

    def test_create_repair_rejects_invalid_status(self):
        # Arrange
        payload = repair_payload(status="unknown")

        # Act
        response = self.client.post(self.list_url, payload, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", response.data)

    def test_user_cannot_list_repairs_created_by_another_user(self):
        # Arrange
        other_user = create_user(email="otro@example.com")
        Repair.objects.create(created_by=other_user, **self.payload)

        # Act
        response = self.client.get(self.list_url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_repair_endpoints_require_authentication(self):
        # Arrange
        anonymous = APIClient()

        # Act
        list_response = anonymous.get(self.list_url)
        detail_response = anonymous.get(self._detail_url(1))

        # Assert
        self.assertEqual(list_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(detail_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_owner_can_partially_update_a_repair_via_patch(self):
        # Arrange
        repair = Repair.objects.create(created_by=self.user, **self.payload)

        # Act
        response = self.client.patch(
            self._detail_url(repair.pk),
            {"status": "completed", "issue_description": "Reparación finalizada."},
            format="json",
        )

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        repair.refresh_from_db()
        self.assertEqual(repair.status, "completed")
        self.assertEqual(repair.issue_description, "Reparación finalizada.")

    def test_owner_can_fully_update_a_repair_via_put(self):
        # Arrange
        repair = Repair.objects.create(created_by=self.user, **self.payload)
        updated_payload = repair_payload(
            customer_name="Ana María Pérez",
            customer_phone="+54 11 9999-8888",
            device_type="MacBook Pro",
            device_model="M1 13",
            serial_number="c02xyz123",
            issue_description="Cambio de batería completado con éxito.",
            status="delivered",
        )

        # Act
        response = self.client.put(
            self._detail_url(repair.pk), updated_payload, format="json"
        )

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        repair.refresh_from_db()
        self.assertEqual(repair.customer_name, "Ana María Pérez")
        self.assertEqual(repair.device_type, "MacBook Pro")
        self.assertEqual(repair.serial_number, "C02XYZ123")
        self.assertEqual(repair.status, "delivered")

    def test_user_cannot_update_another_users_repair(self):
        # Arrange
        other_user = create_user(email="otro@example.com")
        repair = Repair.objects.create(created_by=other_user, **self.payload)

        # Act
        response = self.client.patch(
            self._detail_url(repair.pk), {"status": "completed"}, format="json"
        )

        # Assert
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_can_delete_a_repair(self):
        # Arrange
        repair = Repair.objects.create(created_by=self.user, **self.payload)

        # Act
        response = self.client.delete(self._detail_url(repair.pk))

        # Assert
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Repair.objects.filter(pk=repair.pk).exists())

    def test_user_cannot_delete_another_users_repair(self):
        # Arrange
        other_user = create_user(email="otro@example.com")
        repair = Repair.objects.create(created_by=other_user, **self.payload)

        # Act
        response = self.client.delete(self._detail_url(repair.pk))

        # Assert
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Repair.objects.filter(pk=repair.pk).exists())
