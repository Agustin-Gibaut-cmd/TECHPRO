"""Pruebas de autorización por rol y de los usuarios de prueba."""

from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.management.commands.seed_test_users import DEFAULT_PASSWORD, TEST_USERS
from accounts.roles import (
    ADMIN_ROLE,
    READ_ONLY_ROLE,
    SALES_ROLE,
    TECHNICIAN_ROLE,
)
from tests.support import (
    create_role_user,
    customer_payload,
    inventory_payload,
    repair_payload,
    sale_payload,
    supplier_payload,
)
from workshop.models import Customer

User = get_user_model()


class RoleAuthorizationTests(APITestCase):
    """Valida que el rol de consulta solo pueda leer y que los roles operativos escriban."""

    def setUp(self):
        # Arrange
        self.read_only = create_role_user(
            READ_ONLY_ROLE, "consulta@example.com"
        )
        self.client.force_authenticate(self.read_only)

    def test_read_only_role_can_read_every_resource(self):
        # Arrange
        urls = (
            reverse("repair-list-create"),
            reverse("customer-list-create"),
            reverse("supplier-list-create"),
            reverse("inventory-list-create"),
            reverse("sale-list-create"),
            reverse("report-summary"),
        )

        # Act
        responses = [self.client.get(url) for url in urls]

        # Assert
        for response in responses:
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_read_only_role_cannot_write_any_resource(self):
        # Arrange
        writes = (
            ("repair-list-create", repair_payload()),
            ("customer-list-create", customer_payload()),
            ("supplier-list-create", supplier_payload()),
            ("inventory-list-create", inventory_payload(sku="ROL-001")),
            ("sale-list-create", sale_payload()),
        )

        # Act
        responses = [
            (name, self.client.post(reverse(name), payload, format="json"))
            for name, payload in writes
        ]

        # Assert
        for name, response in responses:
            with self.subTest(endpoint=name):
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_read_only_role_cannot_update_or_delete(self):
        # Arrange
        customer = Customer.objects.create(
            created_by=self.read_only, **customer_payload()
        )
        detail_url = reverse("customer-detail", args=[customer.pk])

        # Act
        patch_response = self.client.patch(
            detail_url, {"phone": "11223344"}, format="json"
        )
        delete_response = self.client.delete(detail_url)

        # Assert
        self.assertEqual(patch_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(delete_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_operational_roles_can_write(self):
        # Arrange
        roles = (ADMIN_ROLE, TECHNICIAN_ROLE, SALES_ROLE)

        # Act
        responses = []
        for index, role in enumerate(roles):
            user = create_role_user(role, f"rol-{index}@example.com")
            self.client.force_authenticate(user)
            responses.append(
                (
                    role,
                    self.client.post(
                        reverse("customer-list-create"),
                        customer_payload(name=f"Cliente {role}"),
                        format="json",
                    ),
                )
            )

        # Assert
        for role, response in responses:
            with self.subTest(role=role):
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class SeedTestUsersCommandTests(APITestCase):
    """Valida que el comando de usuarios de prueba sea idempotente."""

    def test_seed_command_creates_roles_and_is_idempotent(self):
        # Arrange
        output = StringIO()

        # Act
        call_command("seed_test_users", "--force", stdout=output, verbosity=0)
        call_command("seed_test_users", "--force", stdout=output, verbosity=0)

        # Assert
        emails = [email for _, email, _, _ in TEST_USERS]
        self.assertEqual(User.objects.filter(email__in=emails).count(), 4)
        for role, email, _, is_admin in TEST_USERS:
            self.assertTrue(Group.objects.filter(name=role).exists())
            user = User.objects.get(email=email)
            self.assertTrue(user.groups.filter(name=role).exists())
            self.assertEqual(user.is_staff, is_admin)
            self.assertTrue(user.check_password(DEFAULT_PASSWORD))
