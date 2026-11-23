from django.urls import include, path
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request: Request) -> Response:
        return Response({"status": "ok"})


urlpatterns = [
    path("api/health/", HealthCheckView.as_view(), name="health-check"),
    path("api/auth/", include("accounts.urls")),
    path("api/repairs/", include("repairs.urls")),
    path("api/", include("workshop.urls")),
]
