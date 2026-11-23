"""Enrutamiento de endpoints para el módulo de reparaciones.

Define las URLs para listar/crear reparaciones (`/`) y consultar, modificar o
eliminar una reparación por su identificador (`/<id>/`).
"""

from django.urls import path

from .views import RepairListCreateView, RepairUpdateView

urlpatterns = [
    path("", RepairListCreateView.as_view(), name="repair-list-create"),
    path("<int:pk>/", RepairUpdateView.as_view(), name="repair-update"),
]
