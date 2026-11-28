"""Generación de tokens JWT para cuentas."""

from rest_framework_simplejwt.tokens import RefreshToken

from .user import serialize_user


def create_token_response(user) -> dict[str, object]:
    """Genera el par de tokens JWT y el perfil serializado."""
    refresh = RefreshToken.for_user(user)
    return {
        "user": serialize_user(user),
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }
