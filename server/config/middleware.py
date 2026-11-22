from collections.abc import Callable

from django.http import HttpRequest, HttpResponseBase
from django.utils.cache import patch_cache_control


class ApiNoStoreMiddleware:
    def __init__(
        self, get_response: Callable[[HttpRequest], HttpResponseBase]
    ) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponseBase:
        response = self.get_response(request)
        if request.path.startswith("/api/"):
            patch_cache_control(response, no_store=True)
        return response
