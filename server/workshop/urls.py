from django.urls import path

from .views import (
    CustomerDetailView,
    CustomerListCreateView,
    InventoryDetailView,
    InventoryListCreateView,
)

urlpatterns = [
    path("customers/", CustomerListCreateView.as_view(), name="customer-list-create"),
    path("customers/<int:pk>/", CustomerDetailView.as_view(), name="customer-detail"),
    path("inventory/", InventoryListCreateView.as_view(), name="inventory-list-create"),
    path("inventory/<int:pk>/", InventoryDetailView.as_view(), name="inventory-detail"),
]
