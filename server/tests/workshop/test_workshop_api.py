from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from repairs.models import Repair

from workshop.models import Customer, InventoryItem, Sale, Supplier

User = get_user_model()


class WorkshopApiTests(APITestCase):
    customers_url = "/api/customers/"
    inventory_url = "/api/inventory/"
    suppliers_url = "/api/suppliers/"
    sales_url = "/api/sales/"
    reports_url = "/api/reports/summary/"

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

    def test_supplier_create_update_and_delete_are_scoped_to_owner(self):
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

    def test_sale_rejects_nonpositive_quantity_and_negative_price(self):
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
