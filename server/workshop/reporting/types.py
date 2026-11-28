"""Tipos de reportes del taller."""

from typing import TypedDict


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
