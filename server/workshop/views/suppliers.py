"""Vistas de proveedores del taller."""

from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from accounts.roles import RoleAccessPermission

from .mixins import OwnerScopedMixin
from ..models import Supplier
from ..serializers import SupplierSerializer


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
