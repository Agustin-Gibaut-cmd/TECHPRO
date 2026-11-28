"""Vistas de inventario del taller."""

from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from accounts.roles import RoleAccessPermission

from .mixins import OwnerScopedMixin
from ..models import InventoryItem
from ..serializers import InventoryItemSerializer
from ..services import save_inventory_item


class InventoryListCreateView(OwnerScopedMixin, ListCreateAPIView):
    """Lista o crea artículos de inventario."""

    model = InventoryItem
    serializer_class = InventoryItemSerializer
    permission_classes = [RoleAccessPermission]

    def perform_create(self, serializer: InventoryItemSerializer) -> None:
        save_inventory_item(serializer, created_by=self.request.user)


class InventoryDetailView(OwnerScopedMixin, RetrieveUpdateDestroyAPIView):
    """Consulta, actualiza o elimina un artículo de inventario."""

    model = InventoryItem
    serializer_class = InventoryItemSerializer
    permission_classes = [RoleAccessPermission]

    def perform_update(self, serializer: InventoryItemSerializer) -> None:
        save_inventory_item(serializer)
