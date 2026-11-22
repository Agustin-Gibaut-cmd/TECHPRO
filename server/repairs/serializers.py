from rest_framework import serializers

from .models import Repair


class RepairSerializer(serializers.ModelSerializer):
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
