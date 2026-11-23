"""Serializadores para órdenes de reparación.

Mapea la entidad Repair hacia JSON y valida los campos requeridos para el
alta y modificación de servicios técnicos.
"""

from rest_framework import serializers

from .models import Repair


class RepairSerializer(serializers.ModelSerializer):
    """Serializador para operaciones de lectura y escritura de reparaciones."""

    class Meta:
        model = Repair
        fields = (
            "id",
            "customer_name",
            "customer_phone",
            "device_type",
            "device_model",
            "serial_number",
            "issue_description",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")
