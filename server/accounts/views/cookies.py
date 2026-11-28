"""Cookies de autenticación para cuentas."""

from django.conf import settings
from rest_framework.response import Response

SESSION_EXPIRED_MESSAGE = "La sesión expiró."


def set_auth_cookies(response: Response, access: str, refresh: str) -> None:
    """Configura las cookies de acceso y refresco."""
    response["Cache-Control"] = "no-store"
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
    """Elimina las cookies de autenticación."""
    response["Cache-Control"] = "no-store"
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
