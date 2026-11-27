"""Pruebas de integración para el recurso de clientes."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from tests.support import create_user, customer_payload
from workshop.models import Customer


class CustomerApiTests(APITestCase):
    """Valida CRUD, validaciones y aislamiento de clientes por usuario."""

    def setUp(self):
        # Arrange
        self.user = create_user()
        self.client.force_authenticate(self.user)
        self.payload = customer_payload()
        self.list_url = reverse("customer-list-create")

    def _detail_url(self, customer_id: int) -> str:
        return reverse("customer-detail", args=[customer_id])

    def test_customer_crud_is_scoped_to_owner(self):
        # Arrange
        payload = self.payload

        # Act
        created = self.client.post(self.list_url, payload, format="json")
        customer = Customer.objects.get()
        updated = self.client.patch(
            self._detail_url(customer.pk),
            {"phone": "+54 11 9876-5432"},
            format="json",
        )
        customer.refresh_from_db()
        deleted = self.client.delete(self._detail_url(customer.pk))

        # Assert
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(customer.created_by, self.user)
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(customer.phone, "+54 11 9876-5432")
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Customer.objects.exists())

    def test_customer_accepts_blank_optional_fields(self):
        # Arrange
        payload = {"name": "Cliente Simple", "phone": "11223344"}

        # Act
        response = self.client.post(self.list_url, payload, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], "")
        self.assertEqual(response.data["address"], "")

    def test_customer_validates_email_format(self):
        # Arrange
        payload = customer_payload(email="correo-sin-arroba")

        # Act
        response = self.client.post(self.list_url, payload, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_customer_validates_required_fields(self):
        # Arrange
        payload = {"email": "sin-datos@example.com"}

        # Act
        response = self.client.post(self.list_url, payload, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)
        self.assertIn("phone", response.data)

    def test_customer_detail_is_not_visible_to_another_user(self):
        # Arrange
        other_user = create_user(email="otro@example.com")
        customer = Customer.objects.create(created_by=other_user, **self.payload)

        # Act
        response = self.client.get(self._detail_url(customer.pk))

        # Assert
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_customer_list_only_returns_own_records(self):
        # Arrange
        other_user = create_user(email="otro@example.com")
        Customer.objects.create(created_by=other_user, **self.payload)

        # Act
        response = self.client.get(self.list_url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_customer_endpoints_require_authentication(self):
        # Arrange
        anonymous = APIClient()

        # Act
        list_response = anonymous.get(self.list_url)
        detail_response = anonymous.get(self._detail_url(1))

        # Assert
        self.assertEqual(list_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(detail_response.status_code, status.HTTP_401_UNAUTHORIZED)
