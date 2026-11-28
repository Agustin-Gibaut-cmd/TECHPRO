"""Modelo de orden de reparación técnica."""

from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import Q

from .constants import REPAIR_FIELD_BOUNDS, FieldBounds
from .mixins import RepairNormalizationMixin
from .validators import PHONE_VALIDATOR, SERIAL_VALIDATOR, _min_non_whitespace_regex

_PHONE_BOUNDS = REPAIR_FIELD_BOUNDS["customer_phone"]


class RepairStatus(models.TextChoices):
    """Estados del ciclo de reparación."""

    RECEIVED = "received", "Recibido"
    DIAGNOSING = "diagnosing", "En diagnóstico"
    IN_PROGRESS = "in_progress", "En reparación"
    WAITING_PARTS = "waiting_parts", "Esperando repuesto"
    COMPLETED = "completed", "Listo"
    DELIVERED = "delivered", "Entregado"


class Repair(RepairNormalizationMixin, models.Model):
    """Orden de servicio técnico para un dispositivo."""

    Status = RepairStatus

    customer_name = models.CharField(
        max_length=REPAIR_FIELD_BOUNDS["customer_name"].max_len,
        validators=[MinLengthValidator(REPAIR_FIELD_BOUNDS["customer_name"].min_len)],
    )
    customer_phone = models.CharField(
        max_length=_PHONE_BOUNDS.max_len,
        validators=[
            MinLengthValidator(_PHONE_BOUNDS.min_len),
            PHONE_VALIDATOR,
        ],
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
            models.Index(fields=("created_by", "-created_at"), name="repairs_owner_created_idx"),
            models.Index(fields=("status", "-created_at"), name="repairs_status_created_idx"),
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