"""Pruebas de integración para el recurso de inventario."""

from unittest.mock import MagicMock

from django.db import IntegrityError
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient, APITestCase

from tests.support import create_user, inventory_payload
from workshop.models import InventoryItem
from workshop.views import _save_inventory_item


class InventoryApiTests(APITestCase):
    """Valida SKU, stock, precios, colisiones y aislamiento de inventario."""

    def setUp(self):
        # Arrange
        self.user = create_user()
        self.client.force_authenticate(self.user)
        self.payload = inventory_payload()
        self.list_url = reverse("inventory-list-create")

    def _detail_url(self, item_id: int) -> str:
        return reverse("inventory-detail", args=[item_id])

    def test_inventory_create_normalizes_sku_and_rejects_duplicate(self):
        # Arrange
        payload = self.payload
        duplicate_payload = inventory_payload(sku="Cargador-001")

        # Act
        created = self.client.post(self.list_url, payload, format="json")
        duplicate = self.client.post(self.list_url, duplicate_payload, format="json")

        # Assert
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(created.data["sku"], "CARGADOR-001")
        self.assertEqual(InventoryItem.objects.get().created_by, self.user)
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("sku", duplicate.data)

    def test_inventory_sku_normalizes_surrounding_whitespace(self):
        # Arrange
        payload = inventory_payload(sku="   cargador-espacios   ")

        # Act
        response = self.client.post(self.list_url, payload, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["sku"], "CARGADOR-ESPACIOS")

    def test_inventory_update_preserves_same_sku_without_false_duplicate_error(self):
        # Arrange
        item = InventoryItem.objects.create(
            created_by=self.user, **inventory_payload(sku="CARGADOR-001")
        )
        payload = {
            "name": "Cargador USB-C Rápido",
            "sku": "cargador-001",
            "quantity": 10,
            "unit_price": "14000.00",
        }

        # Act
        response = self.client.put(
            self._detail_url(item.pk), payload, format="json"
        )

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item.refresh_from_db()
        self.assertEqual(item.name, "Cargador USB-C Rápido")
        self.assertEqual(item.sku, "CARGADOR-001")

    def test_inventory_allows_zero_stock_and_requires_non_negative_price(self):
        # Arrange
        zero_stock = inventory_payload(
            sku="AGOTADO-001", quantity=0, unit_price="0.00"
        )
        negative_price = inventory_payload(sku="NEGATIVO-001", unit_price="-10.00")

        # Act
        ok_response = self.client.post(self.list_url, zero_stock, format="json")
        error_response = self.client.post(self.list_url, negative_price, format="json")

        # Assert
        self.assertEqual(ok_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(error_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("unit_price", error_response.data)

    def test_inventory_rejects_missing_required_fields(self):
        # Arrange
        payload = {"quantity": 1}

        # Act
        response = self.client.post(self.list_url, payload, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)
        self.assertIn("sku", response.data)

    def test_inventory_update_and_delete(self):
        # Arrange
        item = InventoryItem.objects.create(
            created_by=self.user, **inventory_payload(sku="CARGADOR-001")
        )

        # Act
        updated = self.client.patch(
            self._detail_url(item.pk),
            {"quantity": 5, "unit_price": "11999.90"},
            format="json",
        )
        item.refresh_from_db()
        deleted = self.client.delete(self._detail_url(item.pk))

        # Assert
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(item.quantity, 5)
        self.assertEqual(str(item.unit_price), "11999.90")
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(InventoryItem.objects.exists())

    def test_inventory_detail_is_not_visible_to_another_user(self):
        # Arrange
        other_user = create_user(email="otro@example.com")
        item = InventoryItem.objects.create(
            created_by=other_user, **inventory_payload(sku="AJENO-001")
        )

        # Act
        response = self.client.get(self._detail_url(item.pk))

        # Assert
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_same_sku_is_allowed_for_different_users(self):
        # Arrange
        other_user = create_user(email="otro@example.com")
        InventoryItem.objects.create(
            created_by=other_user, **inventory_payload(sku="CARGADOR-001")
        )

        # Act
        response = self.client.post(self.list_url, self.payload, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(InventoryItem.objects.count(), 2)

    def test_save_inventory_item_converts_db_integrity_error_to_validation_error(self):
        # Arrange
        mock_serializer = MagicMock()
        mock_error = IntegrityError("duplicate key value violates unique constraint")

        class MockDiag:
            constraint_name = "inventory_owner_sku_unique"

        class MockCause(Exception):
            diag = MockDiag()

        mock_error.__cause__ = MockCause()
        mock_serializer.save.side_effect = mock_error

        # Act
        with self.assertRaises(ValidationError) as ctx:
            _save_inventory_item(mock_serializer)

        # Assert
        self.assertIn("sku", ctx.exception.detail)

    def test_inventory_endpoints_require_authentication(self):
        # Arrange
        anonymous = APIClient()

        # Act
        list_response = anonymous.get(self.list_url)
        detail_response = anonymous.get(self._detail_url(1))

        # Assert
        self.assertEqual(list_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(detail_response.status_code, status.HTTP_401_UNAUTHORIZED)
