"""Serializadores de DRF para el módulo de taller."""

from rest_framework import serializers

from .models import (
    Customer,
    InventoryItem,
    MIN_MONEY_VALUE,
    PRICE_DECIMAL_PLACES,
    PRICE_MAX_DIGITS,
    Sale,
    Supplier,
)

MAX_SALE_QUANTITY = 2_147_483_647
DUPLICATE_SKU_MESSAGE = "Ya existe un producto con ese SKU."


class CustomerSerializer(serializers.ModelSerializer):
    """Serializador para consulta y mantenimiento de clientes."""

    class Meta:
        model = Customer
        fields = (
            "id",
            "name",
            "phone",
            "email",
            "address",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class SupplierSerializer(serializers.ModelSerializer):
    """Serializador para gestión de proveedores."""

    class Meta:
        model = Supplier
        fields = (
            "id",
            "name",
            "phone",
            "email",
            "address",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class InventoryItemSerializer(serializers.ModelSerializer):
    """Serializador para artículos de inventario con normalización y chequeo de SKU."""

    class Meta:
        model = InventoryItem
        fields = (
            "id",
            "name",
            "sku",
            "category",
            "description",
            "quantity",
            "min_stock",
            "unit_price",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_sku(self, value: str) -> str:
        """Normaliza el SKU a mayúsculas y verifica unicidad dentro de la cuenta."""
        sku = value.strip().upper()
        queryset = InventoryItem.objects.filter(
            created_by=self.context["request"].user,
            sku=sku,
        )
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError(DUPLICATE_SKU_MESSAGE)
        return sku


class SaleSerializer(serializers.ModelSerializer):
    """Serializador para ventas directas con cálculo de total en el servidor."""

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
        """Retorna el importe total calculado en el modelo."""
        return str(sale.total)