"""Internacionalización y zona horaria."""

from .env import env_str

LANGUAGE_CODE = env_str("LANGUAGE_CODE", "es-ar")
TIME_ZONE = env_str("TIME_ZONE", "America/Argentina/Buenos_Aires")
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
