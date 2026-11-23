"""Rutas de autenticación y sesión de usuario.

Contiene los endpoints necesarios para el flujo de autorización:
- `csrf/`: Emisión del token anti-CSRF para formularios y llamadas seguras.
- `register/`: Creación de nuevas cuentas.
- `login/`: Autenticación con credenciales y seteo de cookies HttpOnly.
- `token/refresh/`: Rotación y renovación transparente de tokens JWT.
- `me/`: Consulta de la identidad del usuario actualmente autenticado.
- `logout/`: Invalidación de tokens y eliminación de cookies de sesión.
"""

from django.urls import path

from .views import (
    CookieTokenRefreshView,
    CsrfTokenView,
    CurrentUserView,
    LoginView,
    LogoutView,
    RegisterView,
)

urlpatterns = [
    path("csrf/", CsrfTokenView.as_view(), name="csrf-token"),
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", CookieTokenRefreshView.as_view(), name="token-refresh"),
    path("me/", CurrentUserView.as_view(), name="current-user"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
