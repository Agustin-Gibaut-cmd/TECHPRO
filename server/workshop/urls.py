"""Rutas de endpoints para la operativa de taller.

Expone las rutas REST para clientes, proveedores, inventario, ventas y reportes:
- `/customers/`: Lista y alta de clientes.
- `/customers/<id>/`: Detalle y modificación de clientes.
- `/suppliers/`: Lista y alta de proveedores.
- `/suppliers/<id>/`: Detalle y modificación de proveedores.
- `/inventory/`: Lista y alta de artículos y stock.
- `/inventory/<id>/`: Detalle y modificación de inventario.
- `/sales/`: Lista y registro de ventas.
- `/sales/<id>/`: Detalle y modificación de ventas.
- `/reports/summary/`: Métricas consolidadas e información para gráficos.
"""

from django.urls import path

from .views import (
    CustomerDetailView,
    CustomerListCreateView,
    InventoryDetailView,
    InventoryListCreateView,
    ReportSummaryView,
    SaleDetailView,
    SaleListCreateView,
    SupplierDetailView,
    SupplierListCreateView,
)

urlpatterns = [
    path("customers/", CustomerListCreateView.as_view(), name="customer-list-create"),
    path("customers/<int:pk>/", CustomerDetailView.as_view(), name="customer-detail"),
    path("suppliers/", SupplierListCreateView.as_view(), name="supplier-list-create"),
    path("suppliers/<int:pk>/", SupplierDetailView.as_view(), name="supplier-detail"),
    path("inventory/", InventoryListCreateView.as_view(), name="inventory-list-create"),
    path("inventory/<int:pk>/", InventoryDetailView.as_view(), name="inventory-detail"),
    path("sales/", SaleListCreateView.as_view(), name="sale-list-create"),
    path("sales/<int:pk>/", SaleDetailView.as_view(), name="sale-detail"),
    path("reports/summary/", ReportSummaryView.as_view(), name="report-summary"),
]
