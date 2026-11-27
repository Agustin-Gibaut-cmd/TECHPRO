"""Contrato de métodos HTTP permitidos por recurso."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from repairs.models import Repair
from tests.support import (
    create_user,
    customer_payload,
    inventory_payload,
    repair_payload,
    sale_payload,
    supplier_payload,
)
from workshop.models import Customer, InventoryItem, Sale, Supplier


class HttpMethodContractTests(APITestCase):
    """Verifica respuestas 405 en métodos no soportados."""

    def setUp(self):
        # Arrange
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_collection_endpoints_reject_put_and_delete(self):
        # Arrange
        collections = (
            "repair-list-create",
            "customer-list-create",
            "supplier-list-create",
            "inventory-list-create",
            "sale-list-create",
        )

        # Act
        responses = [
            (
                self.client.put(reverse(name)),
                self.client.delete(reverse(name)),
            )
            for name in collections
        ]

        # Assert
        for name, (put_response, delete_response) in zip(collections, responses):
            with self.subTest(endpoint=name):
                self.assertEqual(
                    put_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
                )
                self.assertEqual(
                    delete_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
                )

    def test_detail_endpoints_reject_post(self):
        # Arrange
        repair = Repair.objects.create(created_by=self.user, **repair_payload())
        customer = Customer.objects.create(created_by=self.user, **customer_payload())
        supplier = Supplier.objects.create(created_by=self.user, **supplier_payload())
        item = InventoryItem.objects.create(
            created_by=self.user, **inventory_payload(sku="METODO-001")
        )
        sale = Sale.objects.create(created_by=self.user, **sale_payload())
        details = (
            ("repair-update", repair.pk),
            ("customer-detail", customer.pk),
            ("supplier-detail", supplier.pk),
            ("inventory-detail", item.pk),
            ("sale-detail", sale.pk),
        )

        # Act
        responses = [
            (name, self.client.post(reverse(name, args=[pk]), {}, format="json"))
            for name, pk in details
        ]

        # Assert
        for name, response in responses:
            with self.subTest(endpoint=name):
                self.assertEqual(
                    response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
                )

    def test_report_summary_rejects_write_methods(self):
        # Arrange
        url = reverse("report-summary")

        # Act
        responses = (
            self.client.post(url, {}, format="json"),
            self.client.put(url, {}, format="json"),
            self.client.patch(url, {}, format="json"),
            self.client.delete(url),
        )

        # Assert
        for response in responses:
            self.assertEqual(
                response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
            )

    def test_auth_endpoints_reject_unsupported_methods(self):
        # Arrange
        unsupported = (
            ("get", "login"),
            ("get", "register"),
            ("get", "token-refresh"),
            ("get", "logout"),
            ("post", "csrf-token"),
            ("post", "current-user"),
        )

        # Act
        responses = []
        for method_name, url_name in unsupported:
            method = getattr(self.client, method_name)
            response = (
                method(reverse(url_name))
                if method_name == "get"
                else method(reverse(url_name), {}, format="json")
            )
            responses.append((url_name, response))

        # Assert
        for url_name, response in responses:
            with self.subTest(endpoint=url_name):
                self.assertEqual(
                    response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
                )

    def test_health_check_rejects_post(self):
        # Arrange
        url = reverse("health-check")

        # Act
        response = self.client.post(url, {}, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)