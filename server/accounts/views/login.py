"""Vista de inicio de sesión."""

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from ..authentication import enforce_csrf
from ..serializers import LoginSerializer
from ..throttling import LoginRateThrottle
from .cookies import set_auth_cookies


class LoginView(APIView):
    """Autentica credenciales y emite cookies de sesión."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [LoginRateThrottle]

    def get_authenticate_header(self, request: Request) -> str:
        return JWTAuthentication().authenticate_header(request) or "Bearer"

    def post(self, request: Request) -> Response:
        enforce_csrf(request)
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        tokens = serializer.validated_data
        response = Response(
            {"user": tokens["user"]},
            status=status.HTTP_200_OK,
        )
        set_auth_cookies(response, str(tokens["access"]), str(tokens["refresh"]))
        return response
