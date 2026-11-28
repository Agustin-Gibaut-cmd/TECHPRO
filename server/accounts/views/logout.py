"""Vista de cierre de sesión."""

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from django.conf import settings
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from ..authentication import enforce_csrf
from .cookies import clear_auth_cookies


class LogoutView(APIView):
    """Revoca el refresh token y elimina las cookies."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request: Request) -> Response:
        enforce_csrf(request)

        refresh_token = request.COOKIES.get(settings.AUTH_REFRESH_COOKIE)
        if refresh_token is not None:
            try:
                RefreshToken(refresh_token).blacklist()
            except TokenError:
                pass

        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_auth_cookies(response)
        return response
