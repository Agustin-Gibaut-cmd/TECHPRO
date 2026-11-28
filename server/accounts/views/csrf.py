"""Vista de token CSRF."""

from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class CsrfTokenView(APIView):
    """Genera y retorna un token CSRF."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request: Request) -> Response:
        response = Response({"csrfToken": get_token(request._request)})
        response["Cache-Control"] = "no-store"
        return response
