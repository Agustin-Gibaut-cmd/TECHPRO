"""Rate limits específicos para endpoints sensibles de autenticación."""

from rest_framework.throttling import AnonRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """Limita los intentos anónimos de login por dirección IP."""

    scope = "login"
    rate = "5/minute"
