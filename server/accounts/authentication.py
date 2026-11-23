"""Autenticación y seguridad para el módulo de cuentas.

Implementa autenticación JWT sin exponer tokens a JavaScript: las credenciales
se transmiten en cookies HttpOnly con atributos SameSite y Secure. Para mitigar
ataques de Cross-Site Request Forgery (CSRF) derivados del uso de cookies, se
aplica una validación explícita de token CSRF en solicitudes con métodos no seguros.
"""

from django.conf import settings
from rest_framework.authentication import CSRFCheck
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import SAFE_METHODS
from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication

CSRF_FAILURE_MESSAGE = "Token CSRF ausente o inválido."


def enforce_csrf(request: Request) -> None:
    """Verifica el token CSRF en solicitudes entrantes que modifican estado.

    Lanza PermissionDenied si el encabezado o cookie CSRF no coinciden con lo
    esperado por Django.
    """
    check = CSRFCheck(lambda _request: None)
    django_request = request._request
    check.process_request(django_request)
    reason = check.process_view(django_request, None, (), {})
    if reason:
        raise PermissionDenied(CSRF_FAILURE_MESSAGE)


class CookieJWTAuthentication(JWTAuthentication):
    """Autenticador DRF que extrae el token JWT desde la cookie HttpOnly de acceso.

    Si el token es válido y la solicitud usa un método no seguro (POST, PUT, PATCH,
    DELETE), ejecuta inmediatamente la validación CSRF para garantizar que la
    solicitud se originó desde un contexto autorizado.
    """

    def authenticate(self, request: Request):
        cookie_name = getattr(settings, "AUTH_ACCESS_COOKIE", "access_token")
        raw_token = request.COOKIES.get(cookie_name)
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)
        if request.method not in SAFE_METHODS:
            enforce_csrf(request)
        return user, validated_token
