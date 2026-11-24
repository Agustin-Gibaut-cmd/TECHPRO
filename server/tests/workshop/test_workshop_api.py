"""Pruebas de integración para la API de operativa de taller y reportes."""

from unittest.mock import MagicMock

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient, APITestCase

from repairs.models import Repair
from workshop.models import Customer, InventoryItem, Sale, Supplier
from workshop.views import _save_inventory_item

User = get_user_model()


class WorkshopApiTests(APITestCase):
    """Valida clientes, proveedores, inventario, ventas y métricas de taller."""

    customers_url = "/api/customers/"
    inventory_url = "/api/inventory/"
    suppliers_url = "/api/suppliers/"
    sales_url = "/api/sales/"
    reports_url = "/api/reports/summary/"

    def setUp(self):
        """Crea el usuario autenticado principal y los payloads base."""
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
        self.supplier_data = {
            "name": "Distribuidora Central",
            "phone": "+54 11 2222-3333",
            "email": "ventas@central.example",
            "address": "Calle 123",
            "notes": "Entrega semanal.",
        }
        self.sale_data = {
            "customer_name": "Ana Pérez",
            "product_name": "Cargador USB-C",
            "quantity": 2,
            "unit_price": "12500.00",
        }

    def _create_other_user(self):
        """Crea una segunda cuenta para comprobar aislamiento entre talleres."""
        return User.objects.create_user(
            username="otro@example.com",
            email="otro@example.com",
            password="TallerSeguro!2026",
        )

    def test_customer_crud_is_scoped_to_owner(self):
        """Permite crear, actualizar y eliminar clientes propios."""
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

    def test_customer_accepts_blank_optional_fields(self):
        """Permite registrar clientes omitiendo campos opcionales."""
        response = self.client.post(
            self.customers_url,
            {"name": "Cliente Simple", "phone": "11223344"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], "")
        self.assertEqual(response.data["address"], "")

    def test_customer_validates_email_format(self):
        """Rechaza emails con formato inválido."""
        response = self.client.post(
            self.customers_url,
            {
                "name": "Cliente Inv",
                "phone": "11223344",
                "email": "correo-sin-arroba",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_customer_detail_is_not_visible_to_another_user(self):
        """Oculta clientes de otra cuenta devolviendo 404."""
        other_user = self._create_other_user()
        customer = Customer.objects.create(created_by=other_user, **self.customer_data)

        response = self.client.get(f"{self.customers_url}{customer.pk}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_inventory_create_normalizes_sku_and_rejects_duplicate(self):
        """Normaliza el SKU a mayúsculas y rechaza duplicados en la misma cuenta."""
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

    def test_inventory_sku_normalizes_surrounding_whitespace(self):
        """Recorta espacios en blanco alrededor del SKU."""
        response = self.client.post(
            self.inventory_url,
            {**self.inventory_data, "sku": "   cargador-espacios   "},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["sku"], "CARGADOR-ESPACIOS")

    def test_inventory_update_preserves_same_sku_without_false_duplicate_error(self):
        """Permite actualizar un artículo conservando su propio SKU."""
        item = InventoryItem.objects.create(
            created_by=self.user,
            **{**self.inventory_data, "sku": "CARGADOR-001"},
        )
        response = self.client.put(
            f"{self.inventory_url}{item.pk}/",
            {
                "name": "Cargador USB-C Rápido",
                "sku": "cargador-001",
                "quantity": 10,
                "unit_price": "14000.00",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item.refresh_from_db()
        self.assertEqual(item.name, "Cargador USB-C Rápido")
        self.assertEqual(item.sku, "CARGADOR-001")

    def test_inventory_allows_zero_stock_and_requires_non_negative_price(self):
        """Acepta stock 0 y precio 0.00, pero rechaza precios negativos."""
        res_ok = self.client.post(
            self.inventory_url,
            {
                **self.inventory_data,
                "sku": "AGOTADO-001",
                "quantity": 0,
                "unit_price": "0.00",
            },
            format="json",
        )
        self.assertEqual(res_ok.status_code, status.HTTP_201_CREATED)

        res_err = self.client.post(
            self.inventory_url,
            {
                **self.inventory_data,
                "sku": "NEGATIVO-001",
                "unit_price": "-10.00",
            },
            format="json",
        )
        self.assertEqual(res_err.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("unit_price", res_err.data)

    def test_save_inventory_item_converts_db_integrity_error_to_validation_error(self):
        """Convierte una colisión de constraint en BD a ValidationError en 'sku'."""
        mock_serializer = MagicMock()
        mock_error = IntegrityError("duplicate key value violates unique constraint")

        class MockDiag:
            constraint_name = "inventory_owner_sku_unique"

        class MockCause(Exception):
            diag = MockDiag()

        mock_error.__cause__ = MockCause()
        mock_serializer.save.side_effect = mock_error

        with self.assertRaises(ValidationError) as ctx:
            _save_inventory_item(mock_serializer)

        self.assertIn("sku", ctx.exception.detail)

    def test_inventory_update_and_delete(self):
        """Permite editar y borrar artículos de inventario propios."""
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

    def test_supplier_crud_is_scoped_to_owner(self):
        """Permite crear, editar y eliminar proveedores propios."""
        created = self.client.post(self.suppliers_url, self.supplier_data, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)

        supplier = Supplier.objects.get()
        self.assertEqual(supplier.created_by, self.user)

        updated = self.client.patch(
            f"{self.suppliers_url}{supplier.pk}/",
            {"phone": "+54 11 5555-6666"},
            format="json",
        )
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        supplier.refresh_from_db()
        self.assertEqual(supplier.phone, "+54 11 5555-6666")

        deleted = self.client.delete(f"{self.suppliers_url}{supplier.pk}/")
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Supplier.objects.exists())

    def test_sale_crud_calculates_total_and_ignores_owner_input(self):
        """Calcula el total en servidor y asigna created_by al usuario autenticado."""
        created = self.client.post(
            self.sales_url,
            {**self.sale_data, "total": "0.01", "created_by_id": 99999},
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(created.data["total"], "25000.00")

        sale = Sale.objects.get()
        self.assertEqual(sale.created_by, self.user)

        updated = self.client.patch(
            f"{self.sales_url}{sale.pk}/",
            {"quantity": 3},
            format="json",
        )
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(updated.data["total"], "37500.00")

        deleted = self.client.delete(f"{self.sales_url}{sale.pk}/")
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Sale.objects.exists())

    def test_sale_calculates_decimal_precision_accurately(self):
        """Calcula totales decimales exactos sin errores de punto flotante."""
        response = self.client.post(
            self.sales_url,
            {
                "customer_name": "Cliente Decimal",
                "product_name": "Cable Adaptador",
                "quantity": 3,
                "unit_price": "19.99",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["total"], "59.97")

    def test_sale_rejects_nonpositive_quantity_and_negative_price(self):
        """Rechaza cantidades <= 0 y precios unitarios negativos."""
        zero_quantity = self.client.post(
            self.sales_url,
            {**self.sale_data, "quantity": 0},
            format="json",
        )
        negative_price = self.client.post(
            self.sales_url,
            {**self.sale_data, "unit_price": "-1.00"},
            format="json",
        )
        self.assertEqual(zero_quantity.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("quantity", zero_quantity.data)
        self.assertEqual(negative_price.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("unit_price", negative_price.data)

    def test_report_summary_only_includes_the_authenticated_users_data(self):
        """Excluye datos de otros usuarios en el resumen de reportes."""
        other_user = self._create_other_user()

        Sale.objects.create(created_by=self.user, **self.sale_data)
        Sale.objects.create(
            created_by=other_user,
            **{**self.sale_data, "product_name": "Producto ajeno"},
        )
        Supplier.objects.create(created_by=self.user, **self.supplier_data)
        Customer.objects.create(created_by=self.user, **self.customer_data)
        InventoryItem.objects.create(
            created_by=self.user,
            **{**self.inventory_data, "sku": "CARGADOR-001"},
        )
        Supplier.objects.create(created_by=other_user, **self.supplier_data)
        Customer.objects.create(created_by=other_user, **self.customer_data)
        InventoryItem.objects.create(
            created_by=other_user,
            **{**self.inventory_data, "sku": "CARGADOR-001"},
        )
        Repair.objects.create(
            created_by=other_user,
            customer_name="Otro cliente",
            customer_phone="+54 11 1234-5678",
            device_type="Notebook",
            issue_description="Falla de prueba.",
            status=Repair.Status.RECEIVED,
        )

        response = self.client.get(self.reports_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["sales_count"], 1)
        self.assertEqual(response.data["total_revenue"], "25000.00")
        self.assertEqual(response.data["customer_count"], 1)
        self.assertEqual(response.data["supplier_count"], 1)
        self.assertEqual(response.data["inventory_count"], 1)
        self.assertEqual(response.data["repair_count"], 0)
        self.assertEqual(response.data["open_repair_count"], 0)
        self.assertEqual(response.data["top_products"][0]["product_name"], "Cargador USB-C")

    def test_report_aggregates_sales_stock_and_repair_statuses(self):
        """Verifica agregados de ventas, top productos, inventario y reparaciones abiertas."""
        Sale.objects.create(
            created_by=self.user,
            **{**self.sale_data, "quantity": 4, "unit_price": "100.00"},
        )
        Sale.objects.create(
            created_by=self.user,
            **{**self.sale_data, "quantity": 3, "unit_price": "100.00"},
        )
        Sale.objects.create(
            created_by=self.user,
            **{
                **self.sale_data,
                "product_name": "Mouse",
                "quantity": 5,
                "unit_price": "10.00",
            },
        )
        InventoryItem.objects.create