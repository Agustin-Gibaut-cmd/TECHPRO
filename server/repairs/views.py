"""Controladores para la gestión de reparaciones en el taller.

Asegura el aislamiento multitenant filtrando todas las operaciones contra el
usuario autenticado (`created_by=request.user`).
"""

from django.db.models import QuerySet
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from accounts.roles import RoleAccessPermission

from .models import Repair
from .serializers import RepairSerializer


class RepairListCreateView(ListCreateAPIView):
    """Consulta la lista de reparaciones del taller y registra nuevos ingresos."""

    serializer_class = RepairSerializer
    permission_classes = [RoleAccessPermission]

    def get_queryset(self) -> QuerySet[Repair]:
        """Retorna únicamente las reparaciones pertenecientes a la cuenta autenticada."""
        return Repair.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer: RepairSerializer) -> None:
        """Asigna automáticamente al usuario actual como propietario del registro."""
        serializer.save(created_by=self.request.user)


class RepairUpdateView(RetrieveUpdateDestroyAPIView):
    """Permite consultar en detalle, modificar o eliminar una orden de reparación propia."""

    serializer_class = RepairSerializer
    permission_classes = [RoleAccessPermission]

    def get_queryset(self) -> QuerySet[Repair]:
        """Garantiza que un usuario no pueda acceder a reparaciones de otros talleres."""
        return Repair.objects.filter(created_by=self.request.user)
