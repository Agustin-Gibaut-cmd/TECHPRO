"""Controladores REST para la operativa diaria del taller."""

from typing import Any

from django.db import IntegrityError, transaction
from django.db.models import Model, QuerySet
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView

from accounts.roles import RoleAccessPermission

from .models import Customer, InventoryItem, Sale, Supplier
from .reporting import get_dashboard_summary
from .serializers import (
    CustomerSerializer,
    DUPLICATE_SKU_MESSAGE,
    InventoryItemSerializer,
    SaleSerializer,
    SupplierSerializer,
)

SQLITE_UNIQUE_SKU_FRAGMENT = (
    "UNIQUE constraint failed: "
    "workshop_inventoryitem.created_by_id, workshop_inventoryitem.sku"
)
POSTGRES_UNIQUE_SKU_CONSTRAINT = "inventory_owner_sku_unique"


class OwnerScopedMixin:
    """Restringe las operaciones del queryset al usuario autenticado."""

    model: type[Model]

    def get_queryset(self) -> QuerySet[Any]:
        return self.model.objects.filter(created_by=self.request.user)


def _is_duplicate_sku_error(error: IntegrityError) -> bool:
    """Detecta si el IntegrityError corresponde a colisión del SKU por usuario."""
    cause = error.__cause__ or error
    constraint_name = getattr(getattr(cause, "diag", None), "constraint_name", None)
    return (
        constraint_name == POSTGRES_UNIQUE_SKU_CONSTRAINT
        or SQLITE_UNIQUE_SKU_FRAGMENT in str(cause)
    )


def _save_inventory_item(
    serializer: InventoryItemSerializer, **kwargs: Any
) -> None:
    """Persiste un artículo de inventario capturando colisiones de SKU en BD."""
    try:
        with transaction.atomic():
            serializer.save(**kwargs)
    except IntegrityError as error:
        if _is_duplicate_sku_error(error):
            raise ValidationError({"sku": DUPLICATE_SKU_MESSAGE}) from error
        raise


class CustomerListCreateView(OwnerScopedMixin, ListCreateAPIView):
    """Lista o crea clientes de la cuenta autenticada."""

    model = Customer
    serializer_class = CustomerSerializer
    permission_classes = [RoleAccessPermission]

    def perform_create(self, serializer: CustomerSerializer) -> None:
        serializer.save(created_by=self.request.user)


class CustomerDetailView(OwnerScopedMixin, RetrieveUpdateDestroyAPIView):
    """Consulta, actualiza o elimina un cliente propio."""

    model = Customer
    serializer_class = CustomerSerializer
    permission_classes = [RoleAccessPermission]


class SupplierListCreateView(OwnerScopedMixin, ListCreateAPIView):
    """Lista o crea proveedores de la cuenta autenticada."""

    model = Supplier
    serializer_class = SupplierSerializer
    permission_classes = [RoleAccessPermission]

    def perform_create(self, serializer: SupplierSerializer) -> None:
        serializer.save(created_by=self.request.user)


class SupplierDetailView(OwnerScopedMixin, RetrieveUpdateDestroyAPIView):
    """Consulta, actualiza o elimina un proveedor propio."""

    model = Supplier
    serializer_class = SupplierSerializer
    permission_classes = [RoleAccessPermission]


class InventoryListCreateView(OwnerScopedMixin, ListCreateAPIView):
    """Lista o crea artículos de inventario de la cuenta autenticada."""

    model = InventoryItem
    serializer_class = InventoryItemSerializer
    permission_classes = [RoleAccessPermission]

    def perform_create(self, serializer: InventoryItemSerializer) -> None:
        _save_inventory_item(serializer, created_by=self.request.user)


class InventoryDetailView(OwnerScopedMixin, RetrieveUpdateDestroyAPIView):
    """Consulta, actualiza o elimina un artículo de inventario propio."""

    model = InventoryItem
    serializer_class = InventoryItemSerializer
    permission_classes = [RoleAccessPermission]

    def perform_update(self, serializer: InventoryItemSerializer) -> None:
        _save_inventory_item(serializer)


class SaleListCreateView(OwnerScopedMixin, ListCreateAPIView):
    """Lista o registra ventas de la cuenta autenticada."""

    model = Sale
    serializer_class = SaleSerializer
    permission_classes = [RoleAccessPermission]

    def perform_create(self, serializer: SaleSerializer) -> None:
        serializer.save(created_by=self.request.user)


class SaleDetailView(OwnerScopedMixin, RetrieveUpdateDestroyAPIView):
    """Consulta, modifica o elimina una venta propia."""

    model = Sale
    serializer_class = SaleSerializer
    permission_classes = [RoleAccessPermission]


class ReportSummaryView(APIView):
    """Retorna las métricas consolidadas del taller para el usuario autenticado."""

    permission_classes = [RoleAccessPermission]

    def get(self, request: Request) -> Response:
        return Response(get_dashboard_summary(request.user))