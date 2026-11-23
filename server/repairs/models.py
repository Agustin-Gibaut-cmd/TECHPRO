"""Modelos de datos para la gestión y seguimiento de reparaciones técnicas.

Permite registrar equipos recibidos en el taller, diagnosticar problemas,
asociar repuestos y dar seguimiento al ciclo completo de servicio hasta la
entrega al cliente.
"""

from django.conf import settings
from django.db import models

# Constantes de longitud máxima para consistencia en la base de datos
CUSTOMER_NAME_MAX_LENGTH = 120
CUSTOMER_PHONE_MAX_LENGTH = 32
DEVICE_TYPE_MAX_LENGTH = 80
DEVICE_MODEL_MAX_LENGTH = 100
SERIAL_NUMBER_MAX_LENGTH = 100
ISSUE_DESCRIPTION_MAX_LENGTH = 2000
STATUS_MAX_LENGTH = 20


class Repair(models.Model):
    """Representa una orden de servicio técnico para un dispositivo específico."""

    class Status(models.TextChoices):
        """Estados por los que transita un equipo durante su reparación."""

        RECEIVED = "received", "Recibido"
        DIAGNOSING = "diagnosing", "En diagnóstico"
        IN_PROGRESS = "in_progress", "En reparación"
        WAITING_PARTS = "waiting_parts", "Esperando repuesto"
        COMPLETED = "completed", "Listo"
        DELIVERED = "delivered", "Entregado"

    customer_name = models.CharField(max_length=CUSTOMER_NAME_MAX_LENGTH)
    customer_phone = models.CharField(max_length=CUSTOMER_PHONE_MAX_LENGTH)
    device_type = models.CharField(max_length=DEVICE_TYPE_MAX_LENGTH)
    device_model = models.CharField(max_length=DEVICE_MODEL_MAX_LENGTH, blank=True)
    serial_number = models.CharField(max_length=SERIAL_NUMBER_MAX_LENGTH, blank=True)
    issue_description = models.TextField(max_length=ISSUE_DESCRIPTION_MAX_LENGTH)
    status = models.CharField(
        max_length=STATUS_MAX_LENGTH,
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
