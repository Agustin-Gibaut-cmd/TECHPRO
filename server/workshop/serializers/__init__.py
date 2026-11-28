"""Serializadores del módulo de taller."""

from .constants import DUPLICATE_SKU_MESSAGE, MAX_SALE_QUANTITY
from .customer import CustomerSerializer
from .inventory import InventoryItemSerializer
from .sale import SaleSerializer
from .supplier import SupplierSerializer

__all__ = [
    "CustomerSerializer",
    "DUPLICATE_SKU_MESSAGE",
    "InventoryItemSerializer",
    "MAX_SALE_QUANTITY",
    "SaleSerializer",
    "SupplierSerializer",
]
