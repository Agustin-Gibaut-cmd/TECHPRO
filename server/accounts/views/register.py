"""Vista de registro de cuentas."""

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ..authentication import enforce_csrf
from ..serializers import RegisterSerializer, create_token_response
from .cookies import set_auth_cookies


class RegisterView(APIView):
    """Crea una cuenta nueva y establece la sesión."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request: Request) -> Response:
        enforce_csrf(request)
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = create_token_response(user)
        response = Response(
            {"user": tokens["user"]},
            status=status.HTTP_201_CREATED,
        )
        set_auth_cookies(response, str(tokens["access"]), str(tokens["refresh"]))
        return response
