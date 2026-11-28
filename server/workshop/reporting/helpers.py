"""Funciones auxiliares de reportes."""

from datetime import date, datetime, time
from decimal import Decimal

from django.db.models import ExpressionWrapper, F, DecimalField
from django.db.models.functions import TruncMonth
from django.utils import timezone

from .constants import DECIMAL_CENT, DECIMAL_ZERO


def shift_month(month_start: date, offset: int) -> date:
    """Retorna el primer día del mes desplazado `offset` meses."""
    month_index = month_start.year * 12 + month_start.month - 1 + offset
    year, month = divmod(month_index, 12)
    return date(year, month + 1, 1)


def month_boundary(month_start: date) -> datetime:
    """Convierte el inicio de mes a datetime consciente de la zona horaria."""
    return timezone.make_aware(datetime.combine(month_start, time.min))


def line_total_expression() -> ExpressionWrapper:
    """Expresión SQL para calcular quantity * unit_price."""
    return ExpressionWrapper(
        F("quantity") * F("unit_price"),
        output_field=DecimalField(max_digits=20, decimal_places=2),
    )


def format_money(value: Decimal | None) -> str:
    """Formatea un valor decimal a dos decimales."""
    amount = value if value is not None else DECIMAL_ZERO
    return str(amount.quantize(DECIMAL_CENT))
