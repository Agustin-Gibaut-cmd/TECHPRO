"""Constantes de reportes del taller."""

from decimal import Decimal

from django.conf import settings
from repairs.models import Repair

DEFAULT_MONTHS_WINDOW = 6
DEFAULT_TOP_PRODUCTS_LIMIT = 5
DECIMAL_ZERO = Decimal("0.00")
DECIMAL_CENT = Decimal("0.01")
CLOSED_REPAIR_STATUSES = (
    Repair.Status.COMPLETED.value,
    Repair.Status.DELIVERED.value,
)
REPORT_MONTHS_WINDOW = getattr(settings, "REPORT_MONTHS_WINDOW", DEFAULT_MONTHS_WINDOW)
REPORT_TOP_PRODUCTS_LIMIT = getattr(
    settings, "REPORT_TOP_PRODUCTS_LIMIT", DEFAULT_TOP_PRODUCTS_LIMIT
)
