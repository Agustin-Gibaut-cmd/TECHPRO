"""Motor de agregación y generación de reportes analíticos para TECHPRO.

Calcula estadísticas comerciales y operativas en tiempo real:
- Ingresos acumulados y ticket promedio de ventas.
- Serie cronológica mensual de los últimos meses (con relleno en cero para meses sin ventas).
- Ranking de productos más vendidos en unidades e ingresos.
- Estado general del inventario (unidades totales, valorizado y alertas de stock bajo).
- Balance de reparaciones activas frente a reparaciones completadas o entregadas.
"""

from datetime import date, datetime, time
from decimal import Decimal
from typing import TypedDict

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from repairs.models import Repair

from .models import Customer, InventoryItem, Sale, Supplier

User = get_user_model()

DEFAULT_MONTHS_WINDOW = 6
DEFAULT_TOP_PRODUCTS_LIMIT = 5
DECIMAL_ZERO = Decimal("0.00")
DECIMAL_CENT = Decimal("0.01")


class MonthlySales(TypedDict):
    """Estructura para la representación mensual de ventas en gráficos."""

    month: str
    sales_count: int
    revenue: str


class ProductSales(TypedDict):
    """Resumen de desempeño por producto individual."""

    product_name: str
    units_sold: int
    revenue: str


def _shift_month(month_start: date, offset: int) -> date:
    """Calcula el primer día del mes sumando o restando un desplazamiento de meses."""
    month_index = month_start.year * 12 + month_start.month - 1 + offset
    year, month = divmod(month_index, 12)
    return date(year, month + 1, 1)


def _month_boundary(month_start: date) -> datetime:
    """Convierte una fecha de inicio de mes en un datetime consciente de la zona horaria."""
    return timezone.make_aware(datetime.combine(month_start, time.min))


def _sale_total_expression() -> ExpressionWrapper:
    """Construye la expresión SQL para calcular el importe total (cantidad * precio unitario)."""
    return ExpressionWrapper(
        F("quantity") * F("unit_price"),
        output_field=DecimalField(max_digits=20, decimal_places=2),
    )


def _format_money(value: Decimal | None) -> str:
    """Formatea un valor decimal con dos dígitos fraccionarios o retorna 0.00 si es nulo."""
    amount = value if value is not None else DECIMAL_ZERO
    return str(amount.quantize(DECIMAL_CENT))


def get_dashboard_summary(user: User) -> dict[str, object]:
    """Genera las métricas comerciales y de taller consolidadas para el usuario dado.

    Garantiza que la ventana de tiempo refleje los últimos meses continuos sin saltos,
    completando con importes en cero aquellos períodos que no registren ventas.
    """
    months_window = getattr(settings, "REPORT_MONTHS_WINDOW", DEFAULT_MONTHS_WINDOW)
    top_products_limit = getattr(settings, "REPORT_TOP_PRODUCTS_LIMIT", DEFAULT_TOP_PRODUCTS_LIMIT)

    sales = Sale.objects.filter(created_by=user)
    current_month_start = timezone.localdate().replace(day=1)
    first_month_start = _shift_month(current_month_start, -(months_window - 1))
    next_month_start = _shift_month(current_month_start, 1)
    month_starts = [
        _shift_month(first_month_start, offset) for offset in range(months_window)
    ]

    total_sales = sales.count()
    revenue = sales.aggregate(total=Sum(_sale_total_expression()))["total"]
    total_revenue = revenue if revenue is not None else DECIMAL_ZERO
    average_sale = (
        (total_revenue / total_sales).quantize(DECIMAL_CENT)
        if total_sales
        else DECIMAL_ZERO
    )

    monthly_rows = list(
        sales.filter(
            created_at__gte=_month_boundary(first_month_start),
            created_at__lt=_month_boundary(next_month_start),
        )
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(
            sales_count=Count("id"),
            revenue=Sum(_sale_total_expression()),
        )
        .order_by("month")
    )
    monthly_by_key = {
        row["month"].strftime("%Y-%m"): row for row in monthly_rows
    }
    monthly_sales: list[MonthlySales] = []
    for month_start in month_starts:
        month_key = month_start.strftime("%Y-%m")
        row = monthly_by_key.get(month_key, {})
        monthly_sales.append(
            {
                "month": month_key,
                "sales_count": row.get("sales_count", 0),
                "revenue": _format_money(row.get("revenue")),
            }
        )

    product_rows = (
        sales.values("product_name")
        .annotate(
            units_sold=Sum("quantity"),
            revenue=Sum(_sale_total_expression()),
        )
        .order_by("-units_sold", "product_name")[:top_products_limit]
    )
    top_products: list[ProductSales] = [
        {
            "product_name": row["product_name"],
            "units_sold": row["units_sold"],
            "revenue": _format_money(row["revenue"]),
        }
        for row in product_rows
    ]

    inventory = InventoryItem.objects.filter(created_by=user)
    stock_value = inventory.aggregate(
        total=Sum(
            ExpressionWrapper(
                F("quantity") * F("unit_price"),
                output_field=DecimalField(max_digits=20, decimal_places=2),
            )
        )
    )["total"]
    repairs = Repair.objects.filter(created_by=user)

    closed_repair_statuses = (
        Repair.Status.COMPLETED.value,
        Repair.Status.DELIVERED.value,
    )

    return {
        "sales_count": total_sales,
        "total_revenue": _format_money(total_revenue),
        "average_sale": _format_money(average_sale),
        "current_month": current_month_start.strftime("%Y-%m"),
        "monthly_sales": monthly_sales,
        "top_products": top_products,
        "customer_count": Customer.objects.filter(created_by=user).count(),
        "supplier_count": Supplier.objects.filter(created_by=user).count(),
        "inventory_count": inventory.count(),
        "inventory_units": inventory.aggregate(total=Sum("quantity"))["total"] or 0,
        "low_stock_count": inventory.filter(quantity__lte=F("min_stock")).count(),
        "inventory_value": _format_money(stock_value),
        "repair_count": repairs.count(),
        "open_repair_count": repairs.exclude(
            status__in=closed_repair_statuses
        ).count(),
    }
