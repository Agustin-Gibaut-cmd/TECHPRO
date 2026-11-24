"""Pruebas de integración para el módulo de órdenes de reparación (repairs)."""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from repairs.models import Repair

User = get_user_model()


class RepairApiTests(APITestCase):
    """Valida CRUD, normalización, validaciones y aislamiento multitenant en repairs."""

    url = "/api/repairs/"

    def setUp(self):
        """Crea el usuario principal autenticado y un payload base válido."""
        self.user = User.objects.create_user(
            username="ana@example.com",
            email="ana@example.com",
            password="TallerSeguro!2026",
        )
        self.client.force_authenticate(self.user)
        self.payload = {
            "customer_name": "Ana Pérez",
            "customer_phone": "+54 11 1234-5678",
            "device_type": "Notebook",
            "device_model": "ThinkPad T14",
            "serial_number": "sn-123456",
            "issue_description": "No enciende después de una caída.",
            "status": "diagnosing",
        }

    def _create_other_user(self):
        """Crea una segunda cuenta para verificar aislamiento entre talleres."""
        return User.objects.create_user(
            username="otro@example.com",
            email="otro@example.com",
            password="TallerSeguro!2026",
        )

    def test_authenticated_user_can_create_list_and_retrieve_repair(self):
        """Permite crear, listar y consultar por ID una reparación propia normalizada."""
        create_response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_response.data["customer_name"], "Ana Pérez")
        self.assertEqual(create_response.data["serial_number"], "SN-123456")
        self.assertEqual(create_response.data["status"], "diagnosing")
        self.assertEqual(Repair.objects.get().created_by, self.user)

        list_response = self.client.get(self.url)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(list_response.data[0]["id"], create_response.data["id"])

        detail_response = self.client.get(f"{self.url}{create_response.data['id']}/")
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data["id"], create_response.data["id"])

    def test_create_repair_validates_required_fields(self):
        """Rechaza payloads sin customer_name, customer_phone o device_type."""
        incomplete_payload = {
            "device_model": "ThinkPad T14",
            "issue_description": "Sin datos de cliente",
        }
        response = self.client.post(self.url, incomplete_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("customer_name", response.data)
        self.assertIn("customer_phone", response.data)
        self.assertIn("device_type", response.data)

    def test_create_repair_validates_max_description_length(self):
        """Rechaza descripciones que excedan los 2000 caracteres."""
        response = self.client.post(
            self.url,
            {**self.payload, "issue_description": "x" * 2001},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("issue_description", response.data)

    def test_create_repair_validates_phone_and_serial_format(self):
        """Rechaza teléfonos o números de serie con caracteres no permitidos."""
        invalid_phone = self.client.post(
            self.url,
            {**self.payload, "customer_phone": "abc-telefono!"},
            format="json",
        )
        self.assertEqual(invalid_phone.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("customer_phone", invalid_phone.data)

        invalid_serial = self.client.post(
            self.url,
            {**self.payload, "serial_number": "SN$INVALID@123"},
            format="json",
        )
        self.assertEqual(invalid_serial.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("serial_number", invalid_serial.data)

    def test_user_cannot_list_repairs_created_by_another_user(self):
        """No lista reparaciones pertenecientes a otro usuario."""
        other_user = self._create_other_user()
        Repair.objects.create(created_by=other_user, **self.payload)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_repair_endpoints_require_authentication(self):
        """Rechaza acceso anónimo con 401."""
        response = APIClient().get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_status_is_rejected(self):
        """Rechaza estados fuera de Repair.Status."""
        response = self.client.post(
            self.url,
            {**self.payload, "status": "unknown"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", response.data)

    def test_owner_can_partially_update_a_repair_via_patch(self):
        """Permite actualizar campos puntuales de una reparación propia con PATCH."""
        repair = Repair.objects.create(created_by=self.user, **self.payload)

        response = self.client.patch(
            f"{self.url}{repair.pk}/",
            {"status": "completed", "issue_description": "Reparación finalizada."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        repair.refresh_from_db()
        self.assertEqual(repair.status, "completed")
        self.assertEqual(repair.issue_description, "Reparación finalizada.")

    def test_owner_can_fully_update_a_repair_via_put(self):
        """Permite reemplazar todos los campos editables de una reparación propia con PUT."""
        repair = Repair.objects.create(created_by=self.user, **self.payload)
        updated_payload = {
            "customer_name": "Ana María Pérez",
            "customer_phone": "+54 11 9999-8888",
            "device_type": "MacBook Pro",
            "device_model": "M1 13",
            "serial_number": "c02xyz123",
            "issue_description": "Cambio de batería completado con éxito.",
            "status": "delivered",
        }

        response = self.client.put(
            f"{self.url}{repair.pk}/",
            updated_payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        repair.refresh_from_db()
        self.assertEqual(repair.customer_name, "Ana María Pérez")
        self.assertEqual(repair.device_type, "MacBook Pro")
        self.assertEqual(repair.serial_number, "C02XYZ123")
        self.assertEqual(repair.status, "delivered")

    def test_user_cannot_update_another_users_repair(self):
        """Impide modificar reparaciones ajenas devolviendo 404."""
        other_user = self._create_other_user()
        repair = Repair.objects.create(created_by=other_user, **self.payload)

        response = self.client.patch(
            f"{self.url}{repair.pk}/",
            {"status": "completed"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_can_delete_a_repair(self):
        """Permite eliminar una reparación propia y devuelve 204."""
        repair = Repair.objects.create(created_by=self.user, **self.payload)

        response = self.client.delete(f"{self.url}{repair.pk}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Repair.objects.filter(pk=repair.pk).exists())

    def test_user_cannot_delete_another_users_repair(self):
        """Impide borrar reparaciones ajenas devolviendo 404."""
        other_user = self._create_other_user()
        repair = Repair.objects.create(created_by=other_user, **self.payload)

        response = self.client.delete(f"{self.url}{repair.pk}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Repair.objects.filter(pk=repair.pk).exists())