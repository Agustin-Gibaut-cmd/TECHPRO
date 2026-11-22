from django.conf import settings
from django.db import models


class Repair(models.Model):
    class Status(models.TextChoices):
        RECEIVED = "received", "Recibido"
        DIAGNOSING = "diagnosing", "En diagnóstico"
        IN_PROGRESS = "in_progress", "En reparación"
        WAITING_PARTS = "waiting_parts", "Esperando repuesto"
        COMPLETED = "completed", "Listo"
        DELIVERED = "delivered", "Entregado"

    customer_name = models.CharField(max_length=120)
    customer_phone = models.CharField(max_length=32)
    device_type = models.CharField(max_length=80)
    device_model = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    issue_description = models.TextField(max_length=2000)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.RECEIVED,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="repairs",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [
            models.Index(
                fields=("created_by", "-created_at"),
                name="repairs_owner_created_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"Reparación #{self.pk} - {self.device_type}"
