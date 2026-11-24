"""Serializadores para registro, autenticación y perfil de usuarios.

Maneja la validación de contraseñas mediante los validadores estándar de Django,
la normalización estricta de direcciones de correo electrónico y la emisión
segura de pares de tokens JWT (access y refresh).
"""

from typing import Any

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

# Longitudes de campos según estándares RFC y modelos de Django
USER_NAME_MIN_LENGTH = 2
USER_NAME_MAX_LENGTH = 150
USER_EMAIL_MAX_LENGTH = 254
USER_PASSWORD_MAX_LENGTH = 128
DEFAULT_PASSWORD_MIN_LENGTH = 12


def serialize_user(user: Any) -> dict[str, str]:
    """Construye una representación pública del usuario sin campos sensibles."""
    return {
        "name": user.first_name or user.email,
        "email": user.email,
    }


def create_token_response(user: Any) -> dict[str, object]:
    """Genera el par de tokens JWT y el perfil serializado para el usuario."""
    refresh = RefreshToken.for_user(user)
    return {
        "user": serialize_user(user),
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


class RegisterSerializer(serializers.Serializer):
    """Valida y crea una nueva cuenta de usuario en el sistema.

    Exige nombre legible, correo único y una contraseña que cumpla con los
    criterios de complejidad definidos en settings.AUTH_PASSWORD_VALIDATORS.
    """

    name = serializers.CharField(
        min_length=USER_NAME_MIN_LENGTH,
        max_length=USER_NAME_MAX_LENGTH,
        trim_whitespace=True,
    )
    email = serializers.EmailField(max_length=USER_EMAIL_MAX_LENGTH)
    password = serializers.CharField(
        min_length=getattr(settings, "AUTH_PASSWORD_MIN_LENGTH", DEFAULT_PASSWORD_MIN_LENGTH),
        max_length=USER_PASSWORD_MAX_LENGTH,
        trim_whitespace=False,
        write_only=True,
    )

    def validate_email(self, value: str) -> str:
        """Normaliza el email a minúsculas y valida que no esté en uso."""
        normalized_email = value.strip().lower()
        if User.objects.filter(
            Q(username__iexact=normalized_email) | Q(email__iexact=normalized_email)
        ).exists():
            raise serializers.ValidationError("Ese correo ya está registrado.")
        return normalized_email

    def validate(self, attrs: dict[str, str]) -> dict[str, str]:
        """Aplica las reglas de seguridad de Django sobre la contraseña ingresada."""
        email = attrs["email"]
        user = User(first_name=attrs["name"], username=email, email=email)
        try:
            validate_password(attrs["password"], user=user)
        except DjangoValidationError as error:
            raise serializers.ValidationError(
                {"password": list(error.messages)}
            ) from error
        return attrs

    def create(self, validated_data: dict[str, str]) -> Any:
        """Crea el usuario dentro de una transacción atómica para prevenir condiciones de carrera."""
        email = validated_data["email"]
        try:
            with transaction.atomic():
                return User.objects.create_user(
                    username=email,
                    email=email,
                    first_name=validated_data["name"],
                    password=validated_data["password"],
                )
        except IntegrityError as error:
            raise serializers.ValidationError(
                {"email": ["Ese correo ya está registrado."]}
            ) from error


class LoginSerializer(serializers.Serializer):
    """Valida las credenciales de acceso y retorna los tokens JWT correspondientes."""

    email = serializers.EmailField(max_length=USER_EMAIL_MAX_LENGTH)
    password = serializers.CharField(
        max_length=USER_PASSWORD_MAX_LENGTH,
        trim_whitespace=False,
        write_only=True,
    )

    def validate(self, attrs: dict[str, str]) -> dict[str, object]:
        """Verifica que el usuario exista, esté activo y la contraseña sea correcta."""
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