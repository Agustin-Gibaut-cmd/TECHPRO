"""Pruebas de integración para el recurso de ventas."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from tests.support import create_user, sale_payload
from workshop.models import Sale


class SaleApiTests(APITestCase):
    """Valida totales, precisión decimal, validaciones y aislamiento de ventas."""

    def setUp(self):
        # Arrange
        self.user = create_user()
        self.client.force_authenticate(self.user)
        self.payload = sale_payload()
        self.list_url = reverse("sale-list-create")

    def _detail_url(self, sale_id: int) -> str:
        return reverse("sale-detail", args=[sale_id])

    def test_sale_crud_calculates_total_and_ignores_owner_input(self):
        # Arrange
        payload = sale_payload(total="0.01", created_by_id=99999)

        # Act
        created = self.client.post(self.list_url, payload, format="json")
        sale = Sale.objects.get()
        updated = self.client.patch(
            self._detail_url(sale.pk), {"quantity": 3}, format="json"
        )
        deleted = self.client.delete(self._detail_url(sale.pk))

        # Assert
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(created.data["total"], "25000.00")
        self.assertEqual(sale.created_by, self.user)
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(updated.data["total"], "37500.00")
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Sale.objects.exists())

    def test_sale_calculates_decimal_precision_accurately(self):
        # Arrange
        payload = sale_payload(
            customer_name="Cliente Decimal",
            product_name="Cable Adaptador",
            quantity=3,
            unit_price="19.99",
        )

        # Act
        response = self.client.post(self.list_url, payload, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["total"], "59.97")

    def test_sale_rejects_nonpositive_quantity_and_negative_price(self):
        # Arrange
        zero_quantity = sale_payload(quantity=0)
        negative_price = sale_payload(unit_price="-1.00")

        # Act
        quantity_response = self.client.post(
            self.list_url, zero_quantity, format="json"
        )
        price_response = self.client.post(self.list_url, negative_price, format="json")

        # Assert
        self.assertEqual(quantity_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("quantity", quantity_response.data)
        self.assertEqual(price_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("unit_price", price_response.data)

    def test_sale_rejects_missing_required_fields(self):
        # Arrange
        payload = {"customer_name": "Sin producto"}

        # Act
        response = self.client.post(self.list_url, payload, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("product_name", response.data)
        self.assertIn("quantity", response.data)
        self.assertIn("unit_price", response.data)

    def test_sale_detail_is_not_visible_to_another_user(self):
        # Arrange
        other_user = create_user(email="otro@example.com")
        sale = Sale.objects.create(created_by=other_user, **self.payload)

        # Act
        response = self.client.get(self._detail_url(sale.pk))

        # Assert
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_sale_list_only_returns_own_records(self):
        # Arrange
        other_user = create_user(email="otro@example.com")
        Sale.objects.create(created_by=other_user, **self.payload)

        # Act
        response = self.client.get(self.list_url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_sale_endpoints_require_authentication(self):
        # Arrange
        anonymous = APIClient()

        # Act
        list_response = anonymous.get(self.list_url)
        detail_response = anonymous.get(self._detail_url(1))

        # Assert
        self.assertEqual(list_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(detail_response.status_code, status.HTTP_401_UNAUTHORIZED)
