"""Motor de reportes del taller."""

from django.utils import timezone

from .summary import get_dashboard_summary

__all__ = ["get_dashboard_summary", "timezone"]
