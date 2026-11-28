"""Mixins de normalización para reparaciones."""

from django.db import models


class RepairNormalizationMixin:
    """Normaliza y valida una orden de reparación."""

    def _normalize_fields(self) -> None:
        self.customer_name = " ".join(self.customer_name.split())
        self.customer_phone = " ".join(self.customer_phone.split())
        self.device_type = " ".join(self.device_type.split())
        self.device_model = " ".join(self.device_model.split())
        self.serial_number = self.serial_number.strip().upper()
        self.issue_description = self.issue_description.strip()

    def clean(self) -> None:
        self._normalize_fields()
        super().clean()

    def save(self, *args, **kwargs) -> None:
        self._normalize_fields()
        if not kwargs.get("update_fields"):
            self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Reparación #{self.pk} - {self.device_type}"
