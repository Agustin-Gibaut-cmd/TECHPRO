from django.db.models import QuerySet
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated

from .models import Repair
from .serializers import RepairSerializer


class RepairListCreateView(ListCreateAPIView):
    serializer_class = RepairSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Repair]:
        return Repair.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer: RepairSerializer) -> None:
        serializer.save(created_by=self.request.user)


class RepairUpdateView(RetrieveUpdateDestroyAPIView):
    serializer_class = RepairSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Repair]:
        return Repair.objects.filter(created_by=self.request.user)
