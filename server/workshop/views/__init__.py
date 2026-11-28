"""Vistas del módulo de taller."""

from .customers import CustomerDetailView, CustomerListCreateView
from .inventory import InventoryDetailView, InventoryListCreateView
from .mixins import OwnerScopedMixin
from .reports import ReportSummaryView
from .sales import SaleDetailView, SaleListCreateView
from .suppliers import SupplierDetailView, SupplierListCreateView

from ..services import is_duplicate_sku_error, save_inventory_item

# Compatibilidad con pruebas que importan helpers desde workshop.views.
_save_inventory_item = save_inventory_item
_is_duplicate_sku_error = is_duplicate_sku_error

__all__ = [
    "CustomerDetailView",
    "CustomerListCreateView",
    "InventoryDetailView",
    "InventoryListCreateView",
    "OwnerScopedMixin",
    "ReportSummaryView",
    "SaleDetailView",
    "SaleListCreateView",
    "SupplierDetailView",
    "SupplierListCreateView",
    "_is_duplicate_sku_error",
    "_save_inventory_item",
]
