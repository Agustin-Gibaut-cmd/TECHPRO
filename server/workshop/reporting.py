from decimal import Decimal
from typing import TypedDict

from django.contrib.auth import get_user_model
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import TruncMonth

from repairs.models import Repair

from .models import Customer, InventoryItem, Sale, Supplier

User = get_user_model()


class MonthlySales(TypedDict):
    month: str
    sales_count: int
    revenue: str


class ProductSales(TypedDict):
    product_name: str
    units_sold: int
    revenue: str


def _sale_total_expression() -> ExpressionWrapper:
    return ExpressionWrapper(
        F("quantity") * F("unit_price"),
        output_field=DecimalField(max_digits=20, decimal_places=2),
    )


def _format_money(value: Decimal | None) -> str:
    amount = value if value is not None else Decimal("0.00")
    return str(amount.quantize(Decimal("0.01")))


def get_dashboard_summary(user: User) -> dict[str, object]:
    sales = Sale.objects.filter(created_by=user)
    total_sales = sales.count()
    revenue = sales.aggregate(total=Sum(_sale_total_expression()))["total"]
    total_revenue = revenue if revenue is not None else Decimal("0.00")
    average_sale = (
        (total_revenue / total_sales).quantize(Decimal("0.01"))
        if total_sales
        else Decimal("0.00")
    )

    monthly_rows = list(
        sales.annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(
            sales_count=Count("id"),
            revenue=Sum(_sale_total_expression()),
        )
        .order_by("-month")[:6]
    )
    monthly_rows.reverse()
    monthly_sales: list[MonthlySales] = [
        {
            "month": row["month"].strftime("%Y-%m"),
            "sales_count": row["sales_count"],
            "revenue": _format_money(row["revenue"]),
        }
        for row in monthly_rows
    ]

    product_rows = (
        sales.values("product_name")
        .annotate(
            units_sold=Sum("quantity"),
            revenue=Sum(_sale_total_expression()),
        )
        .order_by("-units_sold", "product_name")[:5]
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

    return {
        "sales_count": total_sales,
        "total_revenue": _format_money(total_revenue),
        "average_sale": _format_money(average_sale),
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
            status__in=("completed", "delivered")
        ).count(),
    }
