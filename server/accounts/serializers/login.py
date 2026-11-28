"""Serializador de autenticación de cuentas."""

from django.contrib.auth import authenticate, get_user_model
from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

from .constants import USER_EMAIL_MAX_LENGTH, USER_PASSWORD_MAX_LENGTH
from .tokens import create_token_response

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    """Valida credenciales y retorna tokens JWT."""

    email = serializers.EmailField(max_length=USER_EMAIL_MAX_LENGTH)
    password = serializers.CharField(
        max_length=USER_PASSWORD_MAX_LENGTH,
        trim_whitespace=False,
        write_only=True,
    )

    def validate(self, attrs: dict[str, str]) -> dict[str, object]:
        email = attrs["email"].strip().lower()
        matched_user = (
            User.objects.filter(Q(email__iexact=email) | Q(username__iexact=email))
            .order_by("id")
            .first()
        )
        auth_username = matched_user.username if matched_user is not None else email

        user = authenticate(
            request=self.context.get("request"),
            username=auth_username,
            password=attrs["password"],
        )
        if user is None or not user.is_active:
            raise AuthenticationFailed("Correo o contraseña incorrectos.")

        return create_token_response(user)
