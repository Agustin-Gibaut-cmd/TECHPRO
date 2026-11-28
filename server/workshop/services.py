"""Servicios de dominio para la operación del taller.

Encapsulan reglas de negocio y persistencia que no deben vivir en las vistas ni
en los serializadores.
"""

from django.db import IntegrityError, transaction
from rest_framework.serializers import ValidationError

from .serializers import DUPLICATE_SKU_MESSAGE

SQLITE_UNIQUE_SKU_FRAGMENT = (
    "UNIQUE constraint failed: "
    "workshop_inventoryitem.created_by_id, workshop_inventoryitem.sku"
)
POSTGRES_UNIQUE_SKU_CONSTRAINT = "inventory_owner_sku_unique"


def is_duplicate_sku_error(error: IntegrityError) -> bool:
    """Detecta si el error corresponde a una colisión de SKU por propietario."""
    cause = error.__cause__ or error
    constraint_name = getattr(getattr(cause, "diag", None), "constraint_name", None)
    return (
        constraint_name == POSTGRES_UNIQUE_SKU_CONSTRAINT
        or SQLITE_UNIQUE_SKU_FRAGMENT in str(cause)
    )


def save_inventory_item(serializer, **kwargs) -> None:
    """Persiste un artículo capturando colisiones de SKU a nivel de base de datos."""
    try:
        with transaction.atomic():
            serializer.save(**kwargs)
    except IntegrityError as error:
        if is_duplicate_sku_error(error):
            raise ValidationError({"sku": DUPLICATE_SKU_MESSAGE}) from error
        raise
