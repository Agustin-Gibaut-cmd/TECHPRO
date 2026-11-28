"""Validadores reutilizables para reparaciones."""

import re

from django.core.validators import MinLengthValidator, RegexValidator

from .constants import REPAIR_FIELD_BOUNDS

_PHONE_BOUNDS = REPAIR_FIELD_BOUNDS["customer_phone"]

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
