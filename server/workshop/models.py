from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Customer(models.Model):
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=32)
    email = models.EmailField(max_length=254, blank=True)
    address = models.CharField(max_length=200, blank=True)
    notes = models.TextField(max_length=1000, blank=True)
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
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=32)
    email = models.EmailField(max_length=254, blank=True)
    address = models.CharField(max_length=200, blank=True)
    notes = models.TextField(max_length=1000, blank=True)
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
    name = models.CharField(max_length=120)
    sku = models.CharField(max_length=40)
    category = models.CharField(max_length=80, blank=True)
    description = models.TextField(max_length=1000, blank=True)
    quantity = models.PositiveIntegerField(default=0)
    min_stock = models.PositiveIntegerField(default=0)
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
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
    customer_name = models.CharField(max_length=120, blank=True)
    product_name = models.CharField(max_length=120)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
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
        return self.unit_price * self.quantity

    def __str__(self) -> str:
        return f"{self.product_name} x {self.quantity}"
