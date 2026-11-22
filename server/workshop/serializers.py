from decimal import Decimal

from rest_framework import serializers

from .models import Customer, InventoryItem, Sale, Supplier


class CustomerSerializer(serializers.ModelSerializer):
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
        sku = value.strip().upper()
        queryset = InventoryItem.objects.filter(
            created_by=self.context["request"].user,
            sku=sku,
        )
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("Ya existe un producto con ese SKU.")
        return sku


class SaleSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(min_value=1, max_value=2_147_483_647)
    unit_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.00"),
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
