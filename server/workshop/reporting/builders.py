"""Constructores de series de reportes."""

from datetime import date
from typing import Any

from django.db.models import Count, QuerySet, Sum
from django.db.models.functions import TruncMonth

from .helpers import format_money, line_total_expression, month_boundary, shift_month
from .types import MonthlySales, ProductSales


def build_monthly_sales(
    sales: QuerySet[Any],
    current_month_start: date,
    months_window: int,
) -> list[MonthlySales]:
    """Construye la serie mensual continua."""
    first_month_start = shift_month(current_month_start, -(months_window - 1))
    next_month_start = shift_month(current_month_start, 1)
    month_starts = [
        shift_month(first_month_start, offset) for offset in range(months_window)
    ]

    monthly_rows = list(
        sales.filter(
            created_at__gte=month_boundary(first_month_start),
            created_at__lt=month_boundary(next_month_start),
        )
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(
            sales_count=Count("id"),
            revenue=Sum(line_total_expression()),
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
            "revenue": format_money(
                monthly_by_key.get(month_start.strftime("%Y-%m"), {}).get("revenue")
            ),
        }
        for month_start in month_starts
    ]


def build_top_products(
    sales: QuerySet[Any],
    limit: int,
) -> list[ProductSales]:
    """Obtiene el ranking de productos más vendidos."""
    product_rows = (
        sales.values("product_name")
        .annotate(
            units_sold=Sum("quantity"),
            revenue=Sum(line_total_expression()),
        )
        .order_by("-units_sold", "product_name")[:limit]
    )
    return [
        {
            "product_name": row["product_name"],
            "units_sold": row["units_sold"],
            "revenue": format_money(row["revenue"]),
        }
        for row in product_rows
    ]
