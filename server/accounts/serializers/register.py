"""Serializador de registro de cuentas."""

from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from rest_framework import serializers

from .constants import (
    USER_EMAIL_MAX_LENGTH,
    USER_NAME_MAX_LENGTH,
    USER_NAME_MIN_LENGTH,
    USER_PASSWORD_MAX_LENGTH,
)
from .tokens import create_token_response

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    """Valida y crea una nueva cuenta de usuario."""

    name = serializers.CharField(
        min_length=USER_NAME_MIN_LENGTH,
        max_length=USER_NAME_MAX_LENGTH,
        trim_whitespace=True,
    )
    email = serializers.EmailField(max_length=USER_EMAIL_MAX_LENGTH)
    password = serializers.CharField(
        min_length=getattr(settings, "AUTH_PASSWORD_MIN_LENGTH", 12),
        max_length=USER_PASSWORD_MAX_LENGTH,
        trim_whitespace=False,
        write_only=True,
    )

    def validate_email(self, value: str) -> str:
        normalized_email = value.strip().lower()
        if User.objects.filter(
            Q(username__iexact=normalized_email) | Q(email__iexact=normalized_email)
        ).exists():
            raise serializers.ValidationError("Ese correo ya está registrado.")
        return normalized_email

    def validate(self, attrs: dict[str, str]) -> dict[str, str]:
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
