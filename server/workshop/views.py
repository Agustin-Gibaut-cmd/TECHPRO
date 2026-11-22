from typing import Any

from django.db import IntegrityError, transaction
from django.db.models import QuerySet
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView

from .models import Customer, InventoryItem, Sale, Supplier
from .reporting import get_dashboard_summary
from .serializers import (
    CustomerSerializer,
    InventoryItemSerializer,
    SaleSerializer,
    SupplierSerializer,
)


def _save_inventory_item(
    serializer: InventoryItemSerializer, **kwargs: Any
) -> None:
    try:
        with transaction.atomic():
            serializer.save(**kwargs)
    except IntegrityError as error:
        cause = error.__cause__ or error
        constraint_name = getattr(
            getattr(cause, "diag", None), "constraint_name", None
        )
        sqlite_unique_error = (
            "UNIQUE constraint failed: "
            "workshop_inventoryitem.created_by_id, workshop_inventoryitem.sku"
        )
        if (
            constraint_name == "inventory_owner_sku_unique"
            or sqlite_unique_error in str(cause)
        ):
            raise ValidationError(
                {"sku": "Ya existe un producto con ese SKU."}
            ) from error
        raise


class CustomerListCreateView(ListCreateAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Customer]:
        return Customer.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer: CustomerSerializer) -> None:
        serializer.save(created_by=self.request.user)


class CustomerDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Customer]:
        return Customer.objects.filter(created_by=self.request.user)


class SupplierListCreateView(ListCreateAPIView):
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Supplier]:
        return Supplier.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer: SupplierSerializer) -> None:
        serializer.save(created_by=self.request.user)


class SupplierDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Supplier]:
        return Supplier.objects.filter(created_by=self.request.user)


class InventoryListCreateView(ListCreateAPIView):
    serializer_class = InventoryItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[InventoryItem]:
        return InventoryItem.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer: InventoryItemSerializer) -> None:
        _save_inventory_item(serializer, created_by=self.request.user)


class InventoryDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = InventoryItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[InventoryItem]:
        return InventoryItem.objects.filter(created_by=self.request.user)

    def perform_update(self, serializer: InventoryItemSerializer) -> None:
        _save_inventory_item(serializer)


class SaleListCreateView(ListCreateAPIView):
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Sale]:
        return Sale.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer: SaleSerializer) -> None:
        serializer.save(created_by=self.request.user)


class SaleDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Sale]:
        return Sale.objects.filter(created_by=self.request.user)


class ReportSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response(get_dashboard_summary(request.user))
