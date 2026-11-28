"""Vista de refresco de token JWT."""

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from django.conf import settings
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from ..authentication import enforce_csrf
from .cookies import SESSION_EXPIRED_MESSAGE, set_auth_cookies


class CookieTokenRefreshView(APIView):
    """Renueva el token de acceso rotando tokens."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get_authenticate_header(self, request: Request) -> str:
        return JWTAuthentication().authenticate_header(request) or "Bearer"

    def post(self, request: Request) -> Response:
        enforce_csrf(request)

        refresh = request.COOKIES.get(settings.AUTH_REFRESH_COOKIE)
        if refresh is None:
            response = Response(
                {"detail": SESSION_EXPIRED_MESSAGE},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            response["Cache-Control"] = "no-store"
            return response

        serializer = TokenRefreshSerializer(data={"refresh": refresh})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as error:
            raise InvalidToken(error.args[0]) from error
        tokens = serializer.validated_data
        response = Response(status=status.HTTP_204_NO_CONTENT)
        set_auth_cookies(
            response,
            str(tokens["access"]),
            str(tokens.get("refresh", refresh)),
        )
        return response
