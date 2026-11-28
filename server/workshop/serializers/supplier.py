"""Serializador de proveedores."""

from rest_framework import serializers

from ..models import Supplier


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
