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
