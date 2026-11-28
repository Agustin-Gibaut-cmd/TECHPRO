"""Vista de perfil del usuario autenticado."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers import serialize_user


class CurrentUserView(APIView):
    """Devuelve la información de perfil activa."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response(serialize_user(request.user))
