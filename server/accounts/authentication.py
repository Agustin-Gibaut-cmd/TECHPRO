from django.conf import settings
from rest_framework.authentication import CSRFCheck
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import SAFE_METHODS
from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication


def enforce_csrf(request: Request) -> None:
    check = CSRFCheck(lambda _request: None)
    django_request = request._request
    check.process_request(django_request)
    reason = check.process_view(django_request, None, (), {})
    if reason:
        raise PermissionDenied("CSRF token missing or invalid.")


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request: Request):
        raw_token = request.COOKIES.get(settings.AUTH_ACCESS_COOKIE)
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)
        if request.method not in SAFE_METHODS:
            enforce_csrf(request)
        return user, validated_token
