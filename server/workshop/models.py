"""Pruebas unitarias de métodos en modelos de workshop."""

from decimal import Decimal
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.test import TestCase

from workshop.models import Customer, InventoryItem, Sale, Supplier

User = get_user_model()


class BaseWorkshopModelTestCase(TestCase):
    """Base POO con creación de usuario y aserciones compartidas para modelos."""

    user: AbstractBaseUser

    def setUp(self) -> None:
        # Arrange
        self.user = self._build_user()

    def _build_user(self) -> AbstractBaseUser:
        return User.objects.create_user(
            username="tech_user",
            password="Password123!",
        )

    def _assert_clean_and_str(
        self,
        instance: models.Model,
        expected_fields: dict[str, Any],
        expected_str: str,
    ) -> None:
        # Act
        instance.full_clean()

        # Assert
        for field, expected_value in expected_fields.items():
            with self.subTest(field=field):
                self.assertEqual(getattr(instance, field), expected_value)
        self.assertEqual(str(instance), expected_str)


class CustomerModelTests(BaseWorkshopModelTestCase):
    """Verifica normalización y representación de Customer."""

    def test_clean_and_str(self) -> None:
        # Arrange
        customer = Customer(
            name="  Juan   Pérez  ",
            phone="  351   1234567  ",
            email="  JUAN@Example.COM  ",
            address="  Av.   Colón  100 ",
            created_by=self.user,
        )

        # Act & Assert
        self._assert_clean_and_str(
            instance=customer,
            expected_fields={
                "name": "Juan Pérez",
                "phone": "351 1234567",
                "email": "juan@example.com",
                "address": "Av. Colón 100",
            },
            expected_str="Juan Pérez",
        )


class SupplierModelTests(BaseWorkshopModelTestCase):
    """Verifica normalización y representación de Supplier."""

    def test_clean_and_str(self) -> None:
        # Arrange
        supplier = Supplier(
            name="  Repuestos   Córdoba  ",
            phone="  351   7654321 ",
            email="  VENTAS@Proveedor.COM ",
            address="  Bv.   San Juan  500 ",
            created_by=self.user,
        )

        # Act & Assert
        self._assert_clean_and_str(
            instance=supplier,
            expected_fields={
                "name": "Repuestos Córdoba",
                "phone": "351 7654321",
                "email": "ventas@proveedor.com",
                "address": "Bv. San Juan 500",
            },
            expected_str="Repuestos Córdoba",
        )


class InventoryItemModelTests(BaseWorkshopModelTestCase):
    """Verifica normalización y representación de InventoryItem."""

    def test_clean_and_str(self) -> None:
        # Arrange
        item = InventoryItem(
            name="  Pantalla   OLED  ",
            sku="  scr-001  ",
            category="  Repuestos   Móviles ",
            quantity=5,
            min_stock=2,
            unit_price=Decimal("45000.00"),
            created_by=self.user,
        )

        # Act & Assert
        self._assert_clean_and_str(
            instance=item,
            expected_fields={
                "name": "Pantalla OLED",
                "sku": "SCR-001",
                "category": "Repuestos Móviles",
            },
            expected_str="Pantalla OLED (SCR-001)",
        )


class SaleModelTests(BaseWorkshopModelTestCase):
    """Verifica normalización, cálculo de total y representación de Sale."""

    def test_clean_total_and_str(self) -> None:
        # Arrange
        sale = Sale(
            customer_name="  María   Gómez ",
            product_name="  Cargador   USB-C ",
            quantity=3,
            unit_price=Decimal("12000.00"),
            created_by=self.user,
        )

        # Act & Assert
        self._assert_clean_and_str(
            instance=sale,
            expected_fields={
                "customer_name": "María Gómez",
                "product_name": "Cargador USB-C",
                "total": Decimal("36000.00"),
            },
            expected_str="Cargador USB-C x 3",
        )