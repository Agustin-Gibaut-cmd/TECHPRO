"""Modelos de datos endurecidos para la gestión y seguimiento de reparaciones técnicas.

Permite registrar equipos recibidos en el taller, diagnosticar problemas,
asociar repuestos y dar seguimiento al ciclo completo de servicio hasta la
entrega al cliente, garantizando integridad referencial, saneamiento de datos
y restricciones estrictas a nivel de base de datos.
"""

from typing import NamedTuple

from django.conf import settings
from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models
from django.db.models import Q


class FieldBounds(NamedTuple):
    """Define los límites mínimo y máximo de caracteres para un campo."""

    min_len: int
    max_len: int


# Límites centralizados de dominio para consistencia entre Python, DRF y SQL
REPAIR_FIELD_BOUNDS: dict[str, FieldBounds] = {
    "customer_name": FieldBounds(min_len=2, max_len=120),
    "customer_phone": FieldBounds(min_len=7, max_len=32),
    "device_type": FieldBounds(min_len=2, max_len=80),
    "device_model": FieldBounds(min_len=0, max_len=100),
    "serial_number": FieldBounds(min_len=0, max_len=100),
    "issue_description": FieldBounds(min_len=5, max_len=2000),
    "status": FieldBounds(min_len=1, max_len=20),
}

_PHONE_BOUNDS = REPAIR_FIELD_BOUNDS["customer_phone"]

# Validadores reutilizables sincronizados con los límites del modelo
PHONE_VALIDATOR = RegexValidator(
    regex=rf"^\+?[0-9\s\-()]{{{_PHONE_BOUNDS.min_len},{_PHONE_BOUNDS.max_len}}}$",
    message="El teléfono solo puede contener dígitos, espacios, guiones, paréntesis y un '+' inicial.",
)
SERIAL_VALIDATOR = RegexValidator(
    regex=r"^[A-Za-z0-9\-_./]*$",
    message="El número de serie contiene caracteres no permitidos.",
)


def _min_non_whitespace_regex(min_len: int) -> str:
    """Genera una regex SQL que exige al menos `min_len` caracteres visibles."""
    return rf"^.*(\S.*){{{min_len},}}$"


class RepairStatus(models.TextChoices):
    """Estados por los que transita un equipo durante su reparación."""

    RECEIVED = "received", "Recibido"
    DIAGNOSING = "diagnosing", "En diagnóstico"
    IN_PROGRESS = "in_progress", "En reparación"
    WAITING_PARTS = "waiting_parts", "Esperando repuesto"
    COMPLETED = "completed", "Listo"
    DELIVERED = "delivered", "Entregado"


class Repair(models.Model):
    """Representa una orden de servicio técnico para un dispositivo específico."""

    Status = RepairStatus

    customer_name = models.CharField(
        max_length=REPAIR_FIELD_BOUNDS["customer_name"].max_len,
        validators=[MinLengthValidator(REPAIR_FIELD_BOUNDS["customer_name"].min_len)],
    )
    customer_phone = models.CharField(
        max_length=_PHONE_BOUNDS.max_len,
        validators=[MinLengthValidator(_PHONE_BOUNDS.min_len), PHONE_VALIDATOR],
    )
    device_type = models.CharField(
        max_length=REPAIR_FIELD_BOUNDS["device_type"].max_len,
        validators=[MinLengthValidator(REPAIR_FIELD_BOUNDS["device_type"].min_len)],
    )
    device_model = models.CharField(
        max_length=REPAIR_FIELD_BOUNDS["device_model"].max_len,
        blank=True,
    )
    serial_number = models.CharField(
        max_length=REPAIR_FIELD_BOUNDS["serial_number"].max_len,
        blank=True,
        validators=[SERIAL_VALIDATOR],
    )
    issue_description = models.TextField(
        max_length=REPAIR_FIELD_BOUNDS["issue_description"].max_len,
        validators=[MinLengthValidator(REPAIR_FIELD_BOUNDS["issue_description"].min_len)],
    )
    status = models.CharField(
        max_length=REPAIR_FIELD_BOUNDS["status"].max_len,
        choices=RepairStatus.choices,
        default=RepairStatus.RECEIVED,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
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
            models.Index(
                fields=("status", "-created_at"),
                name="repairs_status_created_idx",
            ),
            models.Index(
                fields=("serial_number",),
                condition=~Q(serial_number=""),
                name="repairs_serial_non_empty_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(status__in=RepairStatus.values),
                name="repairs_valid_status_chk",
            ),
            models.CheckConstraint(
                condition=(
                    Q(customer_name__regex=_min_non_whitespace_regex(REPAIR_FIELD_BOUNDS["customer_name"].min_len))
                    & Q(customer_phone__regex=_min_non_whitespace_regex(_PHONE_BOUNDS.min_len))
                    & Q(device_type__regex=_min_non_whitespace_regex(REPAIR_FIELD_BOUNDS["device_type"].min_len))
                    & Q(issue_description__regex=_min_non_whitespace_regex(REPAIR_FIELD_BOUNDS["issue_description"].min_len))
                ),
                name="repairs_min_trimmed_lengths_chk",
            ),
        ]

    def _normalize_fields(self) -> None:
        """Limpia espacios redundantes y estandariza formatos antes de validar."""
        self.customer_name = " ".join(self.customer_name.split())
        self.customer_phone = " ".join(self.customer_phone.split())
        self.device_type = " ".join(self.device_type.split())
        self.device_model = " ".join(self.device_model.split())
        self.serial_number = self.serial_number.strip().upper()
        self.issue_description = self.issue_description.strip()

    def clean(self) -> None:
        """Normaliza los datos y ejecuta validaciones de dominio."""
        self._normalize_fields()
        super().clean()

    def save(self, *args, **kwargs) -> None:
        """Normaliza y valida el registro completo antes de persistirlo en SQL."""
        self._normalize_fields()
        if not kwargs.get("update_fields"):
            self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Reparación #{self.pk} - {self.device_type}"