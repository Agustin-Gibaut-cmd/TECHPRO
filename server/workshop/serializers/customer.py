"""Serializador de clientes."""

from rest_framework import serializers

from ..models import Customer


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
