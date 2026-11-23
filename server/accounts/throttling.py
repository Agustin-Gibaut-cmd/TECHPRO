"""Control de frecuencia (rate limiting) para endpoints críticos de autenticación.

Previene ataques de fuerza bruta y enumeración de usuarios restringiendo la
cantidad de intentos fallidos que una misma dirección IP puede realizar en un
período determinado.
"""

from django.conf import settings
from rest_framework.throttling import AnonRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """Limita los intentos anónimos de inicio de sesión por dirección IP.

    Obtiene la tasa configurada desde DEFAULT_THROTTLE_RATES['login'] o la variable
    THROTTLE_RATE_LOGIN, evitando valores rígidos en el código fuente.
    """

    scope = "login"

    def get_rate(self) -> str:
        """Determina la tasa límite consultando la configuración del proyecto."""
        rates = getattr(settings, "REST_FRAMEWORK", {}).get("DEFAULT_THROTTLE_RATES", {})
        return rates.get(self.scope) or getattr(settings, "THROTTLE_RATE_LOGIN", "5/minute")
