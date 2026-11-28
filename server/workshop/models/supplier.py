"""Modelo de proveedor del taller."""

from django.conf import settings
from django.db import models


class Supplier(models.Model):
    """Proveedor asociado a un usuario propietario."""

    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=32)
    email = models.EmailField(blank=True, max_length=254)
    address = models.CharField(blank=True, max_length=200)
    notes = models.TextField(blank=True, max_length=1000)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="suppliers",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name", "id")
        indexes = [
            models.Index(fields=("created_by", "name"), name="supplier_owner_name_idx"),
        ]

    def _normalize_fields(self) -> None:
        self.name = " ".join(self.name.split())
        self.phone = " ".join(self.phone.split())
        self.email = self.email.strip().lower()
        self.address = " ".join(self.address.split())
        self.notes = self.notes.strip()

    def clean(self) -> None:
        self._normalize_fields()
        super().clean()

    def save(self, *args, **kwargs) -> None:
        self._normalize_fields()
        if not kwargs.get("update_fields"):
            self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name
