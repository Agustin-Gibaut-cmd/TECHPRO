"""Resumen del dashboard del taller."""

from decimal import Decimal
from django.db.models import F, Sum

from django.contrib.auth import get_user_model
from . import timezone

from repairs.models import Repair
from ..models import Customer, InventoryItem, Sale, Supplier

from .builders import build_monthly_sales, build_top_products
from .constants import (
    CLOSED_REPAIR_STATUSES,
    DECIMAL_CENT,
    DECIMAL_ZERO,
    REPORT_MONTHS_WINDOW,
    REPORT_TOP_PRODUCTS_LIMIT,
)
from .helpers import format_money, line_total_expression, shift_month

User = get_user_model()


def get_dashboard_summary(user: User) -> dict:
    """Genera las métricas consolidadas del taller."""
    sales = Sale.objects.filter(created_by=user)
    inventory = InventoryItem.objects.filter(created_by=user)
    repairs = Repair.objects.filter(created_by=user)

    current_month_start = timezone.localdate().replace(day=1)
    total_sales = sales.count()
    total_revenue = sales.aggregate(total=Sum(line_total_expression()))["total"] or DECIMAL_ZERO
    average_sale = (
        (total_revenue / total_sales).quantize(DECIMAL_CENT)
        if total_sales
        else DECIMAL_ZERO
    )
    stock_value = inventory.aggregate(total=Sum(line_total_expression()))["total"]

    return {
        "sales_count": total_sales,
        "total_revenue": format_money(total_revenue),
        "average_sale": format_money(average_sale),
        "current_month": current_month_start.strftime("%Y-%m"),
        "monthly_sales": build_monthly_sales(sales, current_month_start, REPORT_MONTHS_WINDOW),
        "top_products": build_top_products(sales, REPORT_TOP_PRODUCTS_LIMIT),
        "customer_count": Customer.objects.filter(created_by=user).count(),
        "supplier_count": Supplier.objects.filter(created_by=user).count(),
        "inventory_count": inventory.count(),
        "inventory_units": inventory.aggregate(total=Sum("quantity"))["total"] or 0,
        "low_stock_count": inventory.filter(quantity__lte=F("min_stock")).count(),
        "inventory_value": format_money(stock_value),
        "repair_count": repairs.count(),
        "open_repair_count": repairs.exclude(status__in=CLOSED_REPAIR_STATUSES).count(),
    }
