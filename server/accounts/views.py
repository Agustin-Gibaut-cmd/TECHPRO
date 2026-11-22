from django.conf import settings
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .authentication import enforce_csrf
from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    create_token_response,
    serialize_user,
)


def set_auth_cookies(response: Response, access: str, refresh: str) -> None:
    response.set_cookie(
        settings.AUTH_ACCESS_COOKIE,
        access,
        max_age=int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()),
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path=settings.AUTH_ACCESS_COOKIE_PATH,
    )
    response.set_cookie(
        settings.AUTH_REFRESH_COOKIE,
        refresh,
        max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path=settings.AUTH_REFRESH_COOKIE_PATH,
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(
        settings.AUTH_ACCESS_COOKIE,
        path=settings.AUTH_ACCESS_COOKIE_PATH,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )
    response.delete_cookie(
        settings.AUTH_REFRESH_COOKIE,
        path=settings.AUTH_REFRESH_COOKIE_PATH,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )


class CsrfTokenView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request: Request) -> Response:
        return Response({"csrfToken": get_token(request._request)})


class RegisterView(APIView):
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


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

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


class CookieTokenRefreshView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request: Request) -> Response:
        enforce_csrf(request)
        refresh = request.COOKIES.get(settings.AUTH_REFRESH_COOKIE)
        if refresh is None:
            return Response(
                {"detail": "La sesión expiró."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = TokenRefreshSerializer(data={"refresh": refresh})
        serializer.is_valid(raise_exception=True)
        tokens = serializer.validated_data
        response = Response(status=status.HTTP_204_NO_CONTENT)
        set_auth_cookies(
            response,
            str(tokens["access"]),
            str(tokens.get("refresh", refresh)),
        )
        return response


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response(serialize_user(request.user))


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        refresh_token = request.COOKIES.get(settings.AUTH_REFRESH_COOKIE)
        if refresh_token is None:
            response = Response(
                {"detail": "La sesión expiró."},
                status=status.HTTP_400_BAD_REQUEST,
            )
            clear_auth_cookies(response)
            return response

        try:
            refresh = RefreshToken(refresh_token)
        except TokenError as error:
            response = Response(
                {"refresh": ["El token de renovación no es válido."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
            clear_auth_cookies(response)
            return response

        if str(refresh.get("user_id")) != str(request.user.pk):
            raise PermissionDenied("El token no pertenece al usuario autenticado.")

        try:
            refresh.blacklist()
        except TokenError as error:
            raise ValidationError({"refresh": ["El token ya no es válido."]}) from error

        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_auth_cookies(response)
        return response
