"""Vistas de clientes del taller."""

from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from accounts.roles import RoleAccessPermission

from .mixins import OwnerScopedMixin
from ..models import Customer
from ..serializers import CustomerSerializer


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
