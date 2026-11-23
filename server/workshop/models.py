"""Modelos de datos para la gestión comercial y operativa del taller.

Engloba las entidades esenciales para la operación diaria:
- `Customer`: Directorio de clientes con datos de contacto.
- `Supplier`: Proveedores de repuestos e insumos.
- `InventoryItem`: Control de stock, repuestos, precios y niveles mínimos.
- `Sale`: Registro de ventas directas de productos o accesorios.
"""

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

# Límites de longitud de campos
CONTACT_NAME_MAX_LENGTH = 120
PHONE_MAX_LENGTH = 32
EMAIL_MAX_LENGTH = 254
ADDRESS_MAX_LENGTH = 200
NOTES_MAX_LENGTH = 1000

SKU_MAX_LENGTH = 40
CATEGORY_MAX_LENGTH = 80
DESCRIPTION_MAX_LENGTH = 1000
PRODUCT_NAME_MAX_LENGTH = 120

PRICE_MAX_DIGITS = 10
PRICE_DECIMAL_PLACES = 2
MIN_MONEY_VALUE = Decimal("0.00")


class Customer(models.Model):
    """Cliente del taller al que se le asocian órdenes de servicio y ventas."""

    name = models.CharField(max_length=CONTACT_NAME_MAX_LENGTH)
    phone = models.CharField(max_length=PHONE_MAX_LENGTH)
    email = models.EmailField(max_length=EMAIL_MAX_LENGTH, blank=True)
    address = models.CharField(max_length=ADDRESS_MAX_LENGTH, blank=True)
    notes = models.TextField(max_length=NOTES_MAX_LENGTH, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customers",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name", "id")
        indexes = [
            models.Index(
                fields=("created_by", "name"),
                name="customer_owner_name_idx",
            ),
        ]

    def __str__(self) -> str:
        return self.name


class Supplier(models.Model):
    """Proveedor comercial que suministra repuestos y consumibles para el taller."""

    name = models.CharField(max_length=CONTACT_NAME_MAX_LENGTH)
    phone = models.CharField(max_length=PHONE_MAX_LENGTH)
    email = models.EmailField(max_length=EMAIL_MAX_LENGTH, blank=True)
    address = models.CharField(max_length=ADDRESS_MAX_LENGTH, blank=True)
    notes = models.TextField(max_length=NOTES_MAX_LENGTH, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="suppliers",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name", "id")
        indexes = [
            models.Index(
                fields=("created_by", "name"),
                name="supplier_owner_name_idx",
            ),
        ]

    def __str__(self) -> str:
        return self.name


class InventoryItem(models.Model):
    """Artículo o repuesto del inventario con seguimiento de existencias y precio."""

    name = models.CharField(max_length=CONTACT_NAME_MAX_LENGTH)
    sku = models.CharField(max_length=SKU_MAX_LENGTH)
    category = models.CharField(max_length=CATEGORY_MAX_LENGTH, blank=True)
    description = models.TextField(max_length=DESCRIPTION_MAX_LENGTH, blank=True)
    quantity = models.PositiveIntegerField(default=0)
    min_stock = models.PositiveIntegerField(default=0)
    unit_price = models.DecimalField(
        max_digits=PRICE_MAX_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=MIN_MONEY_VALUE,
        validators=[MinValueValidator(MIN_MONEY_VALUE)],
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="inventory_items",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("created_by", "sku"),
                name="inventory_owner_sku_unique",
            ),
            models.CheckConstraint(
                condition=models.Q(unit_price__gte=0),
                name="inventory_unit_price_nonnegative",
            ),
        ]
        indexes = [
            models.Index(
                fields=("created_by", "name"),
                name="inventory_owner_name_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.sku})"


class Sale(models.Model):
    """Transacción de venta de productos o insumos realizada por el taller."""

    customer_name = models.CharField(max_length=CONTACT_NAME_MAX_LENGTH, blank=True)
    product_name = models.CharField(max_length=PRODUCT_NAME_MAX_LENGTH)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(
        max_digits=PRICE_MAX_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        validators=[MinValueValidator(MIN_MONEY_VALUE)],
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sales",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "-id")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="sale_quantity_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(unit_price__gte=0),
                name="sale_unit_price_nonnegative",
            ),
        ]
        indexes = [
            models.Index(
                fields=("created_by", "created_at"),
                name="sale_owner_created_idx",
            ),
        ]

    @property
    def total(self) -> Decimal:
        """Calcula el importe total de la venta multiplicando precio unitario y cantidad."""
        return self.unit_price * self.quantity

    def __str__(self) -> str:
        return f"{self.product_name} x {self.quantity}"
