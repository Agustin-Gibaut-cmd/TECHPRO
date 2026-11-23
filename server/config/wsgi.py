"""Punto de entrada WSGI para servidores web compatibles (Gunicorn, uWSGI).

Expone la variable `application` utilizada por el servidor de aplicaciones
en entornos de producción y pruebas.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
