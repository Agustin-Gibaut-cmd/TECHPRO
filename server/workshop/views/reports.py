"""Vista de reportes del taller."""

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.roles import RoleAccessPermission

from ..reporting import get_dashboard_summary


class ReportSummaryView(APIView):
    """Retorna las métricas consolidadas del taller."""

    permission_classes = [RoleAccessPermission]

    def get(self, request: Request) -> Response:
        return Response(get_dashboard_summary(request.user))
