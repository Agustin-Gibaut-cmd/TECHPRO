"""Serializador de inventario."""

from rest_framework import serializers

from ..models import InventoryItem
from .constants import DUPLICATE_SKU_MESSAGE


class InventoryItemSerializer(serializers.ModelSerializer):
    """Serializador para artículos de inventario."""

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
            raise serializers.ValidationError(DUPLICATE_SKU_MESSAGE)
        return sku
