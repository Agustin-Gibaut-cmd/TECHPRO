"""Configuración de la aplicación de autenticación y cuentas de usuario."""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Metadatos de la aplicación de cuentas y seguridad en TECHPRO."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
    verbose_name = "Autenticación y Cuentas"
