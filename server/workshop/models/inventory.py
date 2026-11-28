"""Modelo de artículo de inventario."""

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from .constants import MIN_MONEY_VALUE, PRICE_DECIMAL_PLACES, PRICE_MAX_DIGITS


class InventoryItem(models.Model):
    """Artículo de inventario del taller."""

    name = models.CharField(max_length=120)
    sku = models.CharField(max_length=40)
    category = models.CharField(blank=True, max_length=80)
    description = models.TextField(blank=True, max_length=1000)
    quantity = models.PositiveIntegerField(default=0)
    min_stock = models.PositiveIntegerField(default=0)
    unit_price = models.DecimalField(
        max_digits=PRICE_MAX_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=Decimal("0.00"),
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
        indexes = [
            models.Index(fields=("created_by", "name"), name="inventory_owner_name_idx"),
        ]
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

    def _normalize_fields(self) -> None:
        self.name = " ".join(self.name.split())
        self.sku = self.sku.strip().upper()
        self.category = " ".join(self.category.split())
        self.description = self.description.strip()

    def clean(self) -> None:
        self._normalize_fields()
        super().clean()

    def save(self, *args, **kwargs) -> None:
        self._normalize_fields()
        if not kwargs.get("update_fields"):
            self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.name} ({self.sku})"
