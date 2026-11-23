"""Punto de entrada ASGI para servidores asíncronos (Uvicorn, Daphne).

Permite atender peticiones asíncronas y WebSocket si la infraestructura
lo requiere en el futuro.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()
