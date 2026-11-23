"""Middleware para control estricto de caché en respuestas del API.

Evita que navegadores o proxies intermedios almacenen en memoria o disco
información sensible devuelta por los endpoints (datos de clientes, ventas,
reparaciones o tokens JWT).
"""

from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponseBase
from django.utils.cache import patch_cache_control


class ApiNoStoreMiddleware:
    """Añade directivas 'Cache-Control: no-store' a todas las solicitudes del API."""

    def __init__(
        self, get_response: Callable[[HttpRequest], HttpResponseBase]
    ) -> None:
        self.get_response = get_response
        self.api_prefix = getattr(settings, "API_PREFIX", "/api/")

    def __call__(self, request: HttpRequest) -> HttpResponseBase:
        response = self.get_response(request)
        if request.path.startswith(self.api_prefix):
            patch_cache_control(response, no_store=True)
        return response
