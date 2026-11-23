"""Pruebas de integración para la API de gestión de taller y reportes.

Verifica:
- Operaciones CRUD para Clientes, Proveedores, Inventario y Ventas.
- Aislamiento de datos por usuario (multitenant) en todas las secciones comerciales.
- Normalización automática de SKU y rechazo de duplicados por taller.
- Edición de SKU propio sin generar falsos positivos de duplicidad.
- Cálculo de totales de venta en el servidor con precisión decimal exacta.
- Validación de cantidades positivas, stock cero y precios no negativos.
- Manejo robusto de colisiones de SKU a nivel de base de datos (_save_inventory_item).
- Consolidado de métricas para el dashboard de reportes (sin datos simulados).
"""

from datetime import date
from unittest.mock import MagicMock, patch

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
    """Pruebas integrales de la operativa del taller: clientes, stock, ventas y métricas."""

    customers_url = "/api/customers/"
    inventory_url = "/api/inventory/"
    suppliers_url = "/api/suppliers/"
    sales_url = "/api/sales/"
    reports_url = "/api/reports/summary/"

    def setUp(self):
        """Prepara el usuario autenticado y los datos de prueba base."""
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

    def test_customer_create_update_and_delete_are_scoped_to_owner(self):
        """Las altas, modificaciones y bajas de clientes se asocian al usuario autenticado."""
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

    def test_customer_supplier_accepts_blank_optional_fields(self):
        """Permite crear clientes y proveedores omitiendo email, dirección y notas."""
        minimal_customer = {"name": "Cliente Simple", "phone": "11223344"}
        response = self.client.post(self.customers_url, minimal_customer, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], "")
        self.assertEqual(response.data["address"], "")

    def test_customer_supplier_validates_email_format(self):
        """Rechaza cadenas con formato de email inválido."""
        invalid_email_customer = {
            "name": "Cliente Inv",
            "phone": "11223344",
            "email": "correo-sin-arroba",
        }
        response = self.client.post(self.customers_url, invalid_email_customer, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_customer_detail_is_not_visible_to_another_user(self):
        """Un usuario no puede consultar los datos de un cliente creado por otro taller."""
        other_user = User.objects.create_user(
            username="otro@example.com",
            email="otro@example.com",
            password="TallerSeguro!2026",
        )
        customer = Customer.objects.create(created_by=other_user, **self.customer_data)

        response = self.client.get(f"{self.customers_url}{customer.pk}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_inventory_create_normalizes_sku_and_rejects_duplicate(self):
        """El SKU se convierte a mayúsculas y se rechaza si ya existe en la misma cuenta."""
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
        """Elimina espacios en blanco accidentales antes y después del SKU."""
        data = {**self.inventory_data, "sku": "   cargador-espacios   "}
        response = self.client.post(self.inventory_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["sku"], "CARGADOR-ESPACIOS")

    def test_inventory_update_preserves_same_sku_without_false_duplicate_error(self):
        """Actualizar campos de un producto conservando su SKU no detona error de duplicidad."""
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
        """Permite stock en cero pero rechaza precio negativo."""
        valid_zero_stock = {
            **self.inventory_data,
            "sku": "AGOTADO-001",
            "quantity": 0,
            "unit_price": "0.00",
        }
        res_ok = self.client.post(self.inventory_url, valid_zero_stock, format="json")
        self.assertEqual(res_ok.status_code, status.HTTP_201_CREATED)

        negative_price = {
            **self.inventory_data,
            "sku": "NEGATIVO-001",
            "unit_price": "-10.00",
        }
        res_err = self.client.post(self.inventory_url, negative_price, format="json")
        self.assertEqual(res_err.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("unit_price", res_err.data)

    def test_save_inventory_item_converts_db_integrity_error_to_validation_error(self):
        """La función _save_inventory_item captura colisiones de SKU en concurrencia."""
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
        """Permite modificar existencias/precio y eliminar repuestos del inventario propio."""
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

    def test_supplier_create_update_and_delete_are_scoped_to_owner(self):
        """La gestión de proveedores se mantiene aislada bajo la cuenta propietaria."""
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
        """El servidor recalcula el total y asume el creador ignorando valores alterados."""
        data = {
            **self.sale_data,
            "total": "0.01",
            "created_by_id": 99999,
        }
        created = self.client.post(self.sales_url, data, format="json")

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
        """Calcula importes con decimales exactos evitando errores de redondeo de punto flotante."""
        sale_data = {
            "customer_name": "Cliente Decimal",
            "product_name": "Cable Adaptador",
            "quantity": 3,
            "unit_price": "19.99",
        }
        res = self.client.post(self.sales_url, sale_data, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["total"], "59.97")

    def test_sale_rejects_nonpositive_quantity_and_negative_price(self):
        """Rechaza transacciones con cantidad menor a uno o precio unitario negativo."""
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
        """Los agregados del dashboard no computan ventas, stock o clientes de otras cuentas."""
        Sale.objects.create(created_by=self.user, **self.sale_data)
        other_user = User.objects.create_user(
            username="otro@example.com",
            email="otro@example.com",
            password="TallerSeguro!2026",
        )
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
            customer_phone="123456",
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
        """Calcula ventas mensuales, productos destacados, valor de inventario y estado de reparaciones."""
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
        InventoryItem.objects.create(
            created_by=self.user,
            **{
                **self.inventory_data,
                "sku": "STOCK-BAJO",
                "quantity": 2,
                "min_stock": 3,
                "unit_price": "100.00",
            },
        )
        InventoryItem.objects.create(
            created_by=self.user,
            **{
                **self.inventory_data,
                "sku": "STOCK-OK",
                "quantity": 8,
                "min_stock": 2,
                "unit_price": "10.00",
            },
        )
        repair_data = {
            "customer_name": "Ana Pérez",
            "customer_phone": "+54 11 1234-5678",
            "device_type": "Notebook",
            "issue_description": "Falla de prueba.",
        }
        for repair_status in (
            Repair.Status.RECEIVED,
            Repair.Status.WAITING_PARTS,
            Repair.Status.DELIVERED,
        ):
            Repair.objects.create(
                created_by=self.user,
                status=repair_status,
                **repair_data,
            )

        response = self.client.get(self.reports_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["sales_count"], 3)
        self.assertEqual(response.data["total_revenue"], "750.00")
        self.assertEqual(response.data["average_sale"], "250.00")
        self.assertEqual(len(response.data["monthly_sales"]), 6)
        current_month = timezone.localdate().strftime("%Y-%m")
        self.assertEqual(response.data["current_month"], current_month)
        self.assertEqual(response.data["monthly_sales"][-1]["month"], current_month)
        self.assertEqual(response.data["monthly_sales"][-1]["sales_count"], 3)
        self.assertEqual(response.data["monthly_sales"][-1]["revenue"], "750.00")
        self.assertEqual(response.data["top_products"][0]["product_name"], "Cargador USB-C")
        self.assertEqual(response.data["top_products"][0]["units_sold"], 7)
        self.assertEqual(response.data["top_products"][0]["revenue"], "700.00")
        self.assertEqual(response.data["inventory_units"], 10)
        self.assertEqual(response.data["low_stock_count"], 1)
        self.assertEqual(response.data["inventory_value"], "280.00")
        self.assertEqual(response.data["repair_count"], 3)
        self.assertEqual(response.data["open_repair_count"], 2)

    def test_empty_report_has_no_sample_records(self):
        """Un taller recién registrado recibe reportes en cero sin datos simulados."""
        response = self.client.get(self.reports_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("no-store", response["Cache-Control"])
        self.assertEqual(response.data["sales_count"], 0)
        self.assertEqual(response.data["total_revenue"], "0.00")
        current_month = timezone.localdate().strftime("%Y-%m")
        self.assertEqual(response.data["current_month"], current_month)
        self.assertEqual(len(response.data["monthly_sales"]), 6)
        self.assertEqual(
            response.data["monthly_sales"][-1],
            {
                "month": current_month,
                "sales_count": 0,
                "revenue": "0.00",
            },
        )
        self.assertEqual(response.data["top_products"], [])
        self.assertEqual(response.data["customer_count"], 0)
        self.assertEqual(response.data["supplier_count"], 0)

    @patch("workshop.reporting.timezone.localdate", return_value=date(2027, 1, 15))
    def test_month_window_crosses_year_boundary(self, _localdate):
        """Verifica que la ventana de meses continuos cruce correctamente el cambio de año."""
        response = self.client.get(self.reports_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["current_month"], "2027-01")
        self.assertEqual(
            [month["month"] for month in response.data["monthly_sales"]],
            [
                "2026-08",
                "2026-09",
                "2026-10",
                "2026-11",
                "2026-12",
                "2027-01",
            ],
        )

    def test_workshop_endpoints_require_authentication(self):
        """Todos los endpoints de taller exigen sesión autenticada."""
        client = APIClient()

        customers_response = client.get(self.customers_url)
        inventory_response = client.get(self.inventory_url)
        suppliers_response = client.get(self.suppliers_url)
        sales_response = client.get(self.sales_url)
        reports_response = client.get(self.reports_url)

        self.assertEqual(customers_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(inventory_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(suppliers_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(sales_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(reports_response.status_code, status.HTTP_401_UNAUTHORIZED)
