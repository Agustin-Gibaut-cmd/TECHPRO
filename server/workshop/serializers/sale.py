"""Serializador de ventas."""

from rest_framework import serializers

from ..models import MIN_MONEY_VALUE, PRICE_DECIMAL_PLACES, PRICE_MAX_DIGITS, Sale
from .constants import MAX_SALE_QUANTITY


class SaleSerializer(serializers.ModelSerializer):
    """Serializador para ventas directas."""

    quantity = serializers.IntegerField(min_value=1, max_value=MAX_SALE_QUANTITY)
    unit_price = serializers.DecimalField(
        max_digits=PRICE_MAX_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        min_value=MIN_MONEY_VALUE,
    )
    total = serializers.SerializerMethodField()

    class Meta:
        model = Sale
        fields = (
            "id",
            "customer_name",
            "product_name",
            "quantity",
            "unit_price",
            "total",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "total", "created_at", "updated_at")

    def get_total(self, sale: Sale) -> str:
        return str(sale.total)
