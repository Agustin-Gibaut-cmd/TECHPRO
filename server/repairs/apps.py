"""Configuración de la aplicación de reparaciones y órdenes de servicio."""

from django.apps import AppConfig


class RepairsConfig(AppConfig):
    """Metadatos de la aplicación de órdenes de reparación técnica."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "repairs"
    verbose_name = "Órdenes de Reparación"
