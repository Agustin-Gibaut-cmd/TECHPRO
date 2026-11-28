"""Modelo de venta directa del taller."""

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from .constants import MIN_MONEY_VALUE, PRICE_DECIMAL_PLACES, PRICE_MAX_DIGITS


class Sale(models.Model):
    """Venta directa registrada en el taller."""

    customer_name = models.CharField(blank=True, max_length=120)
    product_name = models.CharField(max_length=120)
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
        indexes = [
            models.Index(fields=("created_by", "created_at"), name="sale_owner_created_idx"),
        ]
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

    def _normalize_fields(self) -> None:
        self.customer_name = " ".join(self.customer_name.split())
        self.product_name = " ".join(self.product_name.split())

    def clean(self) -> None:
        self._normalize_fields()
        super().clean()

    def save(self, *args, **kwargs) -> None:
        self._normalize_fields()
        if not kwargs.get("update_fields"):
            self.full_clean()
        super().save(*args, **kwargs)

    @property
    def total(self) -> Decimal:
        return self.quantity * self.unit_price

    def __str__(self) -> str:
        return f"{self.product_name} x {self.quantity}"
