"""Configuración de la aplicación de gestión de taller (clientes, stock, ventas y métricas)."""

from django.apps import AppConfig


class WorkshopConfig(AppConfig):
    """Metadatos de la aplicación de taller en TECHPRO."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "workshop"
    verbose_name = "Gestión de Taller"
