"""Enrutamiento central de URLs para TECHPRO.

Expone las rutas del API agrupadas por dominio:
- `/api/health/`: Comprobación de salud y disponibilidad del servicio.
- `/api/auth/`: Registro, inicio/cierre de sesión y refresco de tokens.
- `/api/repairs/`: Gestión del ciclo de vida de reparaciones.
- `/api/`: Módulos de taller (clientes, inventario, proveedores, ventas y reportes).
"""

from django.urls import include, path
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """Endpoint público y liviano para balanceadores y monitoreo de uptime."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []

    def get(self, request: Request) -> Response:
        return Response({"status": "ok"})


urlpatterns = [
    path("api/health/", HealthCheckView.as_view(), name="health-check"),
    path("api/auth/", include("accounts.urls")),
    path("api/repairs/", include("repairs.urls")),
    path("api/", include("workshop.urls")),
]
