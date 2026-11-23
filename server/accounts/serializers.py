from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


def serialize_user(user) -> dict[str, str]:
    return {
        "name": user.first_name or user.email,
        "email": user.email,
    }


def create_token_response(user) -> dict[str, object]:
    refresh = RefreshToken.for_user(user)
    return {
        "user": serialize_user(user),
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=2, max_length=150, trim_whitespace=True)
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(
        min_length=12,
        max_length=128,
        trim_whitespace=False,
        write_only=True,
    )

    def validate_email(self, value: str) -> str:
        normalized_email = value.strip().lower()
        if User.objects.filter(username__iexact=normalized_email).exists():
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

    def create(self, validated_data: dict[str, str]):
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
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(max_length=128, trim_whitespace=False, write_only=True)

    def validate(self, attrs: dict[str, str]) -> dict[str, object]:
        email = attrs["email"].strip().lower()
        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=attrs["password"],
        )
        if user is None or not user.is_active:
            raise AuthenticationFailed("Correo o contraseña incorrectos.")

        return create_token_response(user)


