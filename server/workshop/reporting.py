"""Motor de agregación y generación de reportes analíticos para TECHPRO."""

from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, TypedDict

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count, DecimalField, ExpressionWrapper, F, QuerySet, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from repairs.models import Repair

from .models import Customer, InventoryItem, Sale, Supplier

User = get_user_model()

DEFAULT_MONTHS_WINDOW = 6
DEFAULT_TOP_PRODUCTS_LIMIT = 5
DECIMAL_ZERO = Decimal("0.00")
DECIMAL_CENT = Decimal("0.01")
CLOSED_REPAIR_STATUSES = (
    Repair.Status.COMPLETED.value,
    Repair.Status.DELIVERED.value,
)


class MonthlySales(TypedDict):
    """Representación mensual de ventas para gráficos."""

    month: str
    sales_count: int
    revenue: str


class ProductSales(TypedDict):
    """Resumen de ventas e ingresos por producto."""

    product_name: str
    units_sold: int
    revenue: str


def _shift_month(month_start: date, offset: int) -> date:
    """Retorna el primer día del mes desplazado `offset` meses."""
    month_index = month_start.year * 12 + month_start.month - 1 + offset
    year, month = divmod(month_index, 12)
    return date(year, month + 1, 1)


def _month_boundary(month_start: date) -> datetime:
    """Convierte el inicio de mes a datetime consciente de la zona horaria."""
    return timezone.make_aware(datetime.combine(month_start, time.min))


def _line_total_expression() -> ExpressionWrapper:
    """Expresión SQL para calcular quantity * unit_price con precisión decimal."""
    return ExpressionWrapper(
        F("quantity") * F("unit_price"),
        output_field=DecimalField(max_digits=20, decimal_places=2),
    )


def _format_money(value: Decimal | None) -> str:
    """Formatea un valor decimal a dos decimales."""
    amount = value if value is not None else DECIMAL_ZERO
    return str(amount.quantize(DECIMAL_CENT))


def _build_monthly_sales(
    sales: QuerySet[Sale],
    current_month_start: date,
    months_window: int,
) -> list[MonthlySales]:
    """Construye la serie mensual continua completando en cero los meses sin ventas."""
    first_month_start = _shift_month(current_month_start, -(months_window - 1))
    next_month_start = _shift_month(current_month_start, 1)
    month_starts = [
        _shift_month(first_month_start, offset) for offset in range(months_window)
    ]

    monthly_rows = list(
        sales.filter(
            created_at__gte=_month_boundary(first_month_start),
            created_at__lt=_month_boundary(next_month_start),
        )
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(
            sales_count=Count("id"),
            revenue=Sum(_line_total_expression()),
        )
        .order_by("month")
    )
    monthly_by_key = {row["month"].strftime("%Y-%m"): row for row in monthly_rows}

    return [
        {
            "month": month_start.strftime("%Y-%m"),
            "sales_count": monthly_by_key.get(month_start.strftime("%Y-%m"), {}).get(
                "sales_count", 0
            ),
            "revenue": _format_money(
                monthly_by_key.get(month_start.strftime("%Y-%m"), {}).get("revenue")
            ),
        }
        for month_start in month_starts
    ]


def _build_top_products(
    sales: QuerySet[Sale],
    limit: int,
) -> list[ProductSales]:
    """Obtiene el ranking de productos más vendidos ordenado por unidades."""
    product_rows = (
        sales.values("product_name")
        .annotate(
            units_sold=Sum("quantity"),
            revenue=Sum(_line_total_expression()),
        )
        .order_by("-units_sold", "product_name")[:limit]
    )
    return [
        {
            "product_name": row["product_name"],
            "units_sold": row["units_sold"],
            "revenue": _format_money(row["revenue"]),
        }
        for row in product_rows
    ]


def get_dashboard_summary(user: User) -> dict[str, Any]:
    """Genera las métricas consolidadas del taller para el usuario autenticado."""
    months_window = getattr(settings, "REPORT_MONTHS_WINDOW", DEFAULT_MONTHS_WINDOW)
    top_products_limit = getattr(
        settings, "REPORT_TOP_PRODUCTS_LIMIT", DEFAULT_TOP_PRODUCTS_LIMIT
    )

    sales = Sale.objects.filter(created_by=user)
    inventory = InventoryItem.objects.filter(created_by=user)
    repairs = Repair.objects.filter(created_by=user)

    current_month_start = timezone.localdate().replace(day=1)
    total_sales = sales.count()
    total_revenue = sales.aggregate(total=Sum(_line_total_expression()))["total"] or DECIMAL_ZERO
    average_sale = (
        (total_revenue / total_sales).quantize(DECIMAL_CENT)
        if total_sales
        else DECIMAL_ZERO
    )
    stock_value = inventory.aggregate(total=Sum(_line_total_expression()))["total"]

    return {
        "sales_count": total_sales,
        "total_revenue": _format_money(total_revenue),
        "average_sale": _format_money(average_sale),
        "current_month": current_month_start.strftime("%Y-%m"),
        "monthly_sales": _build_monthly_sales(sales, current_month_start, months_window),
        "top_products": _build_top_products(sales, top_products_limit),
        "customer_count": Customer.objects.filter(created_by=user).count(),
        "supplier_count": Supplier.objects.filter(created_by=user).count(),
        "inventory_count": inventory.count(),
        "inventory_units": inventory.aggregate(total=Sum("quantity"))["total"] or 0,
        "low_stock_count": inventory.filter(quantity__lte=F("min_stock")).count(),
        "inventory_value": _format_money(stock_value),
        "repair_count": repairs.count(),
        "open_repair_count": repairs.exclude(status__in=CLOSED_REPAIR_STATUSES).count(),
    }