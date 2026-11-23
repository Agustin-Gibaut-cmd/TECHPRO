"""Controladores REST para la operativa diaria del taller.

Incluye vistas para gestionar clientes, proveedores, inventario y ventas,
así como el consolidado de reportes para el dashboard. Todas las operaciones
están aisladas por usuario para garantizar privacidad de datos entre cuentas.
"""

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


def _save_inventory_item(
    serializer: InventoryItemSerializer, **kwargs: Any
) -> None:
    """Guarda un artículo de inventario capturando colisiones de SKU a nivel de base de datos.

    Atiende posibles condiciones de carrera entre la validación del serializador
    y la inserción efectiva en PostgreSQL o SQLite.
    """
    try:
        with transaction.atomic():
            serializer.save(**kwargs)
    except IntegrityError as error:
        cause = error.__cause__ or error
        constraint_name = getattr(
            getattr(cause, "diag", None), "constraint_name", None
        )
        if (
            constraint_name == POSTGRES_UNIQUE_SKU_CONSTRAINT
            or SQLITE_UNIQUE_SKU_FRAGMENT in str(cause)
        ):
            raise ValidationError(
                {"sku": DUPLICATE_SKU_MESSAGE}
            ) from error
        raise


class CustomerListCreateView(ListCreateAPIView):
    """Consulta la lista de clientes o registra uno nuevo para la cuenta actual."""

    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Customer]:
        return Customer.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer: CustomerSerializer) -> None:
        serializer.save(created_by=self.request.user)


class CustomerDetailView(RetrieveUpdateDestroyAPIView):
    """Obtiene, actualiza o da de baja un cliente específico perteneciente al usuario."""

    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Customer]:
        return Customer.objects.filter(created_by=self.request.user)


class SupplierListCreateView(ListCreateAPIView):
    """Lista proveedores existentes o crea un nuevo contacto de proveedor."""

    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Supplier]:
        return Supplier.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer: SupplierSerializer) -> None:
        serializer.save(created_by=self.request.user)


class SupplierDetailView(RetrieveUpdateDestroyAPIView):
    """Consulta, edita o elimina un proveedor asociado al taller del usuario."""

    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Supplier]:
        return Supplier.objects.filter(created_by=self.request.user)


class InventoryListCreateView(ListCreateAPIView):
    """Lista productos en stock y permite incorporar nuevos repuestos o artículos."""

    serializer_class = InventoryItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[InventoryItem]:
        return InventoryItem.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer: InventoryItemSerializer) -> None:
        _save_inventory_item(serializer, created_by=self.request.user)


class InventoryDetailView(RetrieveUpdateDestroyAPIView):
    """Permite ver el detalle, actualizar stock o precios, y eliminar artículos del inventario."""

    serializer_class = InventoryItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[InventoryItem]:
        return InventoryItem.objects.filter(created_by=self.request.user)

    def perform_update(self, serializer: InventoryItemSerializer) -> None:
        _save_inventory_item(serializer)


class SaleListCreateView(ListCreateAPIView):
    """Lista las ventas del taller y registra nuevas ventas de repuestos o servicios."""

    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Sale]:
        return Sale.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer: SaleSerializer) -> None:
        serializer.save(created_by=self.request.user)


class SaleDetailView(RetrieveUpdateDestroyAPIView):
    """Consulta, modifica o anula una transacción de venta registrada."""

    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Sale]:
        return Sale.objects.filter(created_by=self.request.user)


class ReportSummaryView(APIView):
    """Genera las métricas e indicadores de rendimiento agregados para el panel principal."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response(get_dashboard_summary(request.user))
