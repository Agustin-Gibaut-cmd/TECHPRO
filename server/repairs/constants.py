"""Constantes de dominio para reparaciones."""

from typing import NamedTuple


class FieldBounds(NamedTuple):
    """Límites mínimo y máximo de caracteres para un campo."""

    min_len: int
    max_len: int


REPAIR_FIELD_BOUNDS: dict[str, FieldBounds] = {
    "customer_name": FieldBounds(min_len=2, max_len=120),
    "customer_phone": FieldBounds(min_len=7, max_len=32),
    "device_type": FieldBounds(min_len=2, max_len=80),
    "device_model": FieldBounds(min_len=0, max_len=100),
    "serial_number": FieldBounds(min_len=0, max_len=100),
    "issue_description": FieldBounds(min_len=5, max_len=2000),
    "status": FieldBounds(min_len=1, max_len=20),
}
