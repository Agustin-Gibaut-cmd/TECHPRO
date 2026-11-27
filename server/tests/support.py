"""Utilidades compartidas de datos de prueba y usuarios para la suite backend."""

from __future__ import annotations

from itertools import count
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, Group

User = get_user_model()

DEFAULT_TEST_PASSWORD = "TallerSeguro!2026"
_USER_SEQUENCE = count(1)

REPAIR_PAYLOAD: dict[str, Any] = {
    "customer_name": "Ana Pérez",
    "customer_phone": "+54 11 1234-5678",
    "device_type": "Notebook",
    "device_model": "ThinkPad T14",
    "serial_number": "sn-123456",
    "issue_description": "No enciende después de una caída.",
    "status": "diagnosing",
}

CUSTOMER_PAYLOAD: dict[str, Any] = {
    "name": "Ana Pérez",
    "phone": "+54 11 1234-5678",
    "email": "ana@example.com",
    "address": "Av. Siempre Viva 123",
    "notes": "Prefiere contacto por teléfono.",
}

SUPPLIER_PAYLOAD: dict[str, Any] = {
    "name": "Distribuidora Central",
    "phone": "+54 11 2222-3333",
    "email": "ventas@central.example",
    "address": "Calle 123",
    "notes": "Entrega semanal.",
}

INVENTORY_PAYLOAD: dict[str, Any] = {
    "name": "Cargador USB-C",
    "sku": "cargador-001",
    "category": "Accesorios",
    "description": "Cargador de 65 W.",
    "quantity": 8,
    "min_stock": 2,
    "unit_price": "12500.00",
}

SALE_PAYLOAD: dict[str, Any] = {
    "customer_name": "Ana Pérez",
    "product_name": "Cargador USB-C",
    "quantity": 2,
    "unit_price": "12500.00",
}


class PayloadFactory:
    """Construye payloads de prueba a partir de plantillas base y sobrescrituras."""

    @staticmethod
    def build(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
        """Devuelve una copia del payload base aplicando los campos indicados."""
        return {**base, **overrides}


class TestUserFactory:
    """Crea usuarios de prueba y asigna grupos de rol de forma consistente."""

    @staticmethod
    def next_unique_email() -> str:
        """Genera un correo único cuando el test no especifica uno."""
        index = next(_USER_SEQUENCE)
        return f"operador{index}@example.com"

    @classmethod
    def create_user(
        cls,
        email: str | None = None,
        password: str = DEFAULT_TEST_PASSWORD,
        **extra: Any,
    ) -> AbstractBaseUser:
        """Crea un usuario con username y email sincronizados."""
        resolved_email = email or cls.next_unique_email()
        return User.objects.create_user(
            username=resolved_email,
            email=resolved_email,
            password=password,
            **extra,
        )

    @classmethod
    def create_role_user(
        cls,
        role: str,
        email: str | None = None,
        password: str = DEFAULT_TEST_PASSWORD,
        **extra: Any,
    ) -> AbstractBaseUser:
        """Crea un usuario y lo asocia al grupo correspondiente al rol."""
        group, _ = Group.objects.get_or_create(name=role)
        user = cls.create_user(email=email, password=password, **extra)
        user.groups.add(group)
        return user


def repair_payload(**overrides: Any) -> dict[str, Any]:
    """Retorna un payload válido para órdenes de reparación."""
    return PayloadFactory.build(REPAIR_PAYLOAD, overrides)


def customer_payload(**overrides: Any) -> dict[str, Any]:
    """Retorna un payload válido para clientes."""
    return PayloadFactory.build(CUSTOMER_PAYLOAD, overrides)


def supplier_payload(**overrides: Any) -> dict[str, Any]:
    """Retorna un payload válido para proveedores."""
    return PayloadFactory.build(SUPPLIER_PAYLOAD, overrides)


def inventory_payload(**overrides: Any) -> dict[str, Any]:
    """Retorna un payload válido para ítems de inventario."""
    return PayloadFactory.build(INVENTORY_PAYLOAD, overrides)


def sale_payload(**overrides: Any) -> dict[str, Any]:
    """Retorna un payload válido para ventas."""
    return PayloadFactory.build(SALE_PAYLOAD, overrides)


def create_user(
    email: str | None = None,
    password: str = DEFAULT_TEST_PASSWORD,
    **extra: Any,
) -> AbstractBaseUser:
    """Atajo de compatibilidad para crear un usuario de prueba."""
    return TestUserFactory.create_user(email=email, password=password, **extra)


def create_role_user(
    role: str,
    email: str | None = None,
    password: str = DEFAULT_TEST_PASSWORD,
    **extra: Any,
) -> AbstractBaseUser:
    """Atajo de compatibilidad para crear un usuario asignado a un rol."""
    return TestUserFactory.create_role_user(
        role=role,
        email=email,
        password=password,
        **extra,
    )