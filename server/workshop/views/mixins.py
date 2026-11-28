"""Mixins compartidos de vistas del taller."""

from typing import Any

from django.db.models import Model, QuerySet


class OwnerScopedMixin:
    """Restringe el queryset al usuario autenticado."""

    model: type[Model]

    def get_queryset(self) -> QuerySet[Any]:
        return self.model.objects.filter(created_by=self.request.user)
