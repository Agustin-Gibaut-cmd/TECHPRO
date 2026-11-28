"""Vistas de ventas del taller."""

from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from accounts.roles import RoleAccessPermission

from .mixins import OwnerScopedMixin
from ..models import Sale
from ..serializers import SaleSerializer


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
