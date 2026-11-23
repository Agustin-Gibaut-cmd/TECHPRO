"""Pruebas de integración para la API de reparaciones técnicas.

Valida las reglas del dominio de servicio técnico:
- Creación y listado de reparaciones por usuario autenticado.
- Aislamiento de datos entre talleres (imposibilidad de ver, editar o borrar reparaciones ajenas).
- Validación de campos requeridos y restricciones de longitud.
- Validación de estados permitidos en el flujo de trabajo técnico.
- Actualizaciones parciales (PATCH) y totales (PUT).
- Restricción de acceso sin autenticación previa.
"""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from repairs.models import Repair

User = get_user_model()


class RepairApiTests(APITestCase):
    """Batería de pruebas para el ciclo de vida de órdenes de reparación."""

    url = "/api/repairs/"

    def setUp(self):
        """Crea un usuario de prueba autenticado y prepara un payload estándar."""
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
            "serial_number": "SN-123456",
            "issue_description": "No enciende después de una caída.",
            "status": "diagnosing",
        }

    def test_authenticated_user_can_create_and_list_a_repair(self):
        """Un usuario autenticado puede registrar una reparación y verla en su listado."""
        create_response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_response.data["customer_name"], "Ana Pérez")
        self.assertEqual(create_response.data["status"], "diagnosing")
        self.assertEqual(Repair.objects.get().created_by, self.user)

        list_response = self.client.get(self.url)

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(list_response.data[0]["id"], create_response.data["id"])

    def test_create_repair_validates_required_fields(self):
        """Exige customer_name, customer_phone y device_type obligatoriamente."""
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
        """Rechaza descripciones que superen los 2000 caracteres de límite."""
        oversized = {
            **self.payload,
            "issue_description": "x" * 2001,
        }
        response = self.client.post(self.url, oversized, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("issue_description", response.data)

    def test_user_cannot_list_repairs_created_by_another_user(self):
        """El listado no expone reparaciones cargadas por otros usuarios o talleres."""
        other_user = User.objects.create_user(
            username="otro@example.com",
            email="otro@example.com",
            password="TallerSeguro!2026",
        )
        Repair.objects.create(created_by=other_user, **self.payload)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_repair_endpoints_require_authentication(self):
        """Las peticiones anónimas a la API de reparaciones son rechazadas con HTTP 401."""
        response = APIClient().get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_status_is_rejected(self):
        """Rechaza valores de estado que no figuren en las opciones válidas de Repair.Status."""
        response = self.client.post(
            self.url,
            {**self.payload, "status": "unknown"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", response.data)

    def test_owner_can_partially_update_a_repair(self):
        """El usuario creador de la orden puede modificar parcialmente los datos vía PATCH."""
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
        """Permite actualizar la totalidad de los datos de una reparación mediante PUT."""
        repair = Repair.objects.create(created_by=self.user, **self.payload)
        updated_payload = {
            "customer_name": "Ana María Pérez",
            "customer_phone": "+54 11 9999-8888",
            "device_type": "MacBook Pro",
            "device_model": "M1 13",
            "serial_number": "C02XYZ123",
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
        self.assertEqual(repair.status, "delivered")

    def test_user_cannot_update_another_users_repair(self):
        """Un usuario no puede modificar reparaciones creadas por otra cuenta (devuelve HTTP 404)."""
        other_user = User.objects.create_user(
            username="otro@example.com",
            email="otro@example.com",
            password="TallerSeguro!2026",
        )
        repair = Repair.objects.create(created_by=other_user, **self.payload)

        response = self.client.patch(
            f"{self.url}{repair.pk}/",
            {"status": "completed"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_can_delete_a_repair(self):
        """El propietario puede eliminar una orden de reparación registrada en su taller."""
        repair = Repair.objects.create(created_by=self.user, **self.payload)

        response = self.client.delete(f"{self.url}{repair.pk}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Repair.objects.filter(pk=repair.pk).exists())

    def test_user_cannot_delete_another_users_repair(self):
        """Se impide eliminar reparaciones ajenas respondiendo con HTTP 404."""
        other_user = User.objects.create_user(
            username="otro@example.com",
            email="otro@example.com",
            password="TallerSeguro!2026",
        )
        repair = Repair.objects.create(created_by=other_user, **self.payload)

        response = self.client.delete(f"{self.url}{repair.pk}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Repair.objects.filter(pk=repair.pk).exists())
