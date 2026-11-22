from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Customer, InventoryItem

User = get_user_model()


class WorkshopApiTests(APITestCase):
    customers_url = "/api/customers/"
    inventory_url = "/api/inventory/"

    def setUp(self):
        self.user = User.objects.create_user(
            username="ana@example.com",
            email="ana@example.com",
            password="TallerSeguro!2026",
        )
        self.client.force_authenticate(self.user)
        self.customer_data = {
            "name": "Ana Pérez",
            "phone": "+54 11 1234-5678",
            "email": "ana@example.com",
            "address": "Av. Siempre Viva 123",
            "notes": "Prefiere contacto por teléfono.",
        }
        self.inventory_data = {
            "name": "Cargador USB-C",
            "sku": "cargador-001",
            "category": "Accesorios",
            "description": "Cargador de 65 W.",
            "quantity": 8,
            "min_stock": 2,
            "unit_price": "12500.00",
        }

    def test_customer_create_update_and_delete_are_scoped_to_owner(self):
        created = self.client.post(self.customers_url, self.customer_data, format="json")

        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        customer = Customer.objects.get()
        self.assertEqual(customer.created_by, self.user)

        updated = self.client.patch(
            f"{self.customers_url}{customer.pk}/",
            {"phone": "+54 11 9876-5432"},
            format="json",
        )
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        customer.refresh_from_db()
        self.assertEqual(customer.phone, "+54 11 9876-5432")

        deleted = self.client.delete(f"{self.customers_url}{customer.pk}/")
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Customer.objects.exists())

    def test_customer_detail_is_not_visible_to_another_user(self):
        other_user = User.objects.create_user(
            username="otro@example.com",
            email="otro@example.com",
            password="TallerSeguro!2026",
        )
        customer = Customer.objects.create(created_by=other_user, **self.customer_data)

        response = self.client.get(f"{self.customers_url}{customer.pk}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_inventory_create_normalizes_sku_and_rejects_duplicate(self):
        created = self.client.post(self.inventory_url, self.inventory_data, format="json")

        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(created.data["sku"], "CARGADOR-001")
        self.assertEqual(InventoryItem.objects.get().created_by, self.user)

        duplicate = self.client.post(
            self.inventory_url,
            {**self.inventory_data, "sku": "Cargador-001"},
            format="json",
        )

        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("sku", duplicate.data)

    def test_inventory_update_and_delete(self):
        item = InventoryItem.objects.create(
            created_by=self.user,
            **{**self.inventory_data, "sku": "CARGADOR-001"},
        )

        updated = self.client.patch(
            f"{self.inventory_url}{item.pk}/",
            {"quantity": 5, "unit_price": "11999.90"},
            format="json",
        )
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 5)
        self.assertEqual(str(item.unit_price), "11999.90")

        deleted = self.client.delete(f"{self.inventory_url}{item.pk}/")
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(InventoryItem.objects.exists())

    def test_workshop_endpoints_require_authentication(self):
        self.client.force_authenticate(user=None)

        customers_response = self.client.get(self.customers_url)
        inventory_response = self.client.get(self.inventory_url)

        self.assertEqual(customers_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(inventory_response.status_code, status.HTTP_401_UNAUTHORIZED)
