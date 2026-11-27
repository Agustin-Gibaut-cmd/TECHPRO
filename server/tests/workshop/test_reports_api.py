"""Pruebas de integración para el resumen de reportes del dashboard."""

from datetime import date
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from repairs.models import Repair
from tests.support import (
    create_user,
    customer_payload,
    inventory_payload,
    sale_payload,
    supplier_payload,
)
from workshop.models import Customer, InventoryItem, Sale, Supplier


class ReportSummaryApiTests(APITestCase):
    """Valida métricas, series mensuales y aislamiento por usuario."""

    def setUp(self):
        # Arrange
        self.user = create_user()
        self.client.force_authenticate(self.user)
        self.url = reverse("report-summary")
        self.sale_data = sale_payload()

    def test_report_summary_only_includes_the_authenticated_users_data(self):
        # Arrange
        other_user = create_user(email="otro@example.com")
        Sale.objects.create(created_by=self.user, **self.sale_data)
        Sale.objects.create(
            created_by=other_user,
            **sale_payload(product_name="Producto ajeno"),
        )
        Supplier.objects.create(created_by=self.user, **supplier_payload())
        Customer.objects.create(created_by=self.user, **customer_payload())
        InventoryItem.objects.create(
            created_by=self.user, **inventory_payload(sku="CARGADOR-001")
        )
        Supplier.objects.create(created_by=other_user, **supplier_payload())
        Customer.objects.create(created_by=other_user, **customer_payload())
        InventoryItem.objects.create(
            created_by=other_user, **inventory_payload(sku="CARGADOR-001")
        )
        Repair.objects.create(
            created_by=other_user,
            customer_name="Otro cliente",
            customer_phone="+54 11 1234-5678",
            device_type="Notebook",
            issue_description="Falla de prueba.",
            status=Repair.Status.RECEIVED,
        )

        # Act
        response = self.client.get(self.url)

        # Assert
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
        # Arrange
        Sale.objects.create(
            created_by=self.user,
            **sale_payload(quantity=4, unit_price="100.00"),
        )
        Sale.objects.create(
            created_by=self.user,
            **sale_payload(quantity=3, unit_price="100.00"),
        )
        Sale.objects.create(
            created_by=self.user,
            **sale_payload(
                product_name="Mouse", quantity=5, unit_price="10.00"
            ),
        )
        InventoryItem.objects.create(
            created_by=self.user,
            **inventory_payload(
                sku="STOCK-BAJO",
                quantity=2,
                min_stock=3,
                unit_price="100.00",
            ),
        )
        InventoryItem.objects.create(
            created_by=self.user,
            **inventory_payload(
                sku="STOCK-OK",
                quantity=8,
                min_stock=2,
                unit_price="10.00",
            ),
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
                created_by=self.user, status=repair_status, **repair_data
            )

        # Act
        response = self.client.get(self.url)

        # Assert
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
        # Act
        response = self.client.get(self.url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("no-store", response["Cache-Control"])
        self.assertEqual(response.data["sales_count"], 0)
        self.assertEqual(response.data["total_revenue"], "0.00")
        current_month = timezone.localdate().strftime("%Y-%m")
        self.assertEqual(response.data["current_month"], current_month)
        self.assertEqual(len(response.data["monthly_sales"]), 6)
        self.assertEqual(
            response.data["monthly_sales"][-1],
            {"month": current_month, "sales_count": 0, "revenue": "0.00"},
        )
        self.assertEqual(response.data["top_products"], [])
        self.assertEqual(response.data["customer_count"], 0)
        self.assertEqual(response.data["supplier_count"], 0)

    @patch("workshop.reporting.timezone.localdate", return_value=date(2027, 1, 15))
    def test_month_window_crosses_year_boundary(self, _localdate):
        # Act
        response = self.client.get(self.url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["current_month"], "2027-01")
        self.assertEqual(
            [month["month"] for month in response.data["monthly_sales"]],
            ["2026-08", "2026-09", "2026-10", "2026-11", "2026-12", "2027-01"],
        )

    def test_report_requires_authentication(self):
        # Arrange
        anonymous = APIClient()

        # Act
        response = anonymous.get(self.url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
