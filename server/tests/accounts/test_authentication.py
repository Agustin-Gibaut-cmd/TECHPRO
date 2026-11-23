"""Pruebas de integración para los flujos de autenticación y seguridad en cuentas.

Verifica el ciclo completo de autenticación:
- Registro de usuarios con validación de contraseña robusta (longitud, similitud, numérica, común).
- Inicio de sesión y asignación de tokens JWT en cookies HttpOnly.
- Renovación transparente mediante refresh token y rotación de credenciales.
- Detección de reuso de tokens (mitigación de ataques de repetición / replay attacks).
- Detección de intentos sospechosos con limitación de tasa (rate limiting).
- Cierre de sesión y revocación inmediata en lista negra (blacklist).
- Obligatoriedad del token CSRF en métodos de modificación de estado.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

from accounts.throttling import LoginRateThrottle

User = get_user_model()


class AuthenticationApiTests(APITestCase):
    """Conjunto de pruebas para validar los endpoints de autenticación y sesiones."""

    csrf_url = "/api/auth/csrf/"
    register_url = "/api/auth/register/"
    login_url = "/api/auth/login/"

    def setUp(self):
        """Inicializa credenciales válidas para las pruebas y limpia la caché de rate limit."""
        cache.clear()
        self.credentials = {
            "name": "Ana Pérez",
            "email": "ana@example.com",
            "password": "TallerSeguro!2026",
        }

    def post_with_csrf(self, url: str, data: dict):
        """Ejecuta una petición POST adjuntando el token CSRF obtenido previamente."""
        csrf_response = self.client.get(self.csrf_url)
        self.assertEqual(csrf_response["Cache-Control"], "no-store")
        return self.client.post(
            url,
            data,
            format="json",
            HTTP_X_CSRFTOKEN=csrf_response.data["csrfToken"],
        )

    def test_registration_creates_user_and_sets_http_only_jwt_cookies(self):
        """El registro crea la cuenta y setea cookies HttpOnly con flags de seguridad."""
        response = self.post_with_csrf(self.register_url, self.credentials)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"]["email"], self.credentials["email"])
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)
        self.assertNotIn("password", response.data)
        self.assertTrue(response.cookies["access_token"]["httponly"])
        self.assertTrue(response.cookies["refresh_token"]["httponly"])
        self.assertEqual(response.cookies["access_token"]["path"], "/api/")
        self.assertEqual(response.cookies["refresh_token"]["path"], "/api/auth/")
        self.assertEqual(response["Cache-Control"], "no-store")

        user = User.objects.get(email=self.credentials["email"])
        self.assertTrue(user.check_password(self.credentials["password"]))

    def test_registration_rejects_case_insensitive_duplicate_email(self):
        """No permite registrar una cuenta con un correo duplicado indistinto de mayúsculas."""
        self.post_with_csrf(self.register_url, self.credentials)
        duplicate = {**self.credentials, "email": "ANA@example.com"}

        response = self.post_with_csrf(self.register_url, duplicate)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_registration_rejects_short_password(self):
        """Rechaza contraseñas que no alcancen la longitud mínima configurada."""
        credentials = {**self.credentials, "password": "short"}

        response = self.post_with_csrf(self.register_url, credentials)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertFalse(User.objects.filter(email=self.credentials["email"]).exists())

    def test_registration_rejects_numeric_only_password(self):
        """Rechaza contraseñas compuestas únicamente por números."""
        credentials = {**self.credentials, "password": "123456789012"}

        response = self.post_with_csrf(self.register_url, credentials)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_registration_rejects_password_similar_to_email(self):
        """Rechaza contraseñas con alta similitud al correo electrónico del usuario."""
        credentials = {**self.credentials, "password": "ana_example_com_pass"}

        response = self.post_with_csrf(self.register_url, credentials)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_registration_rejects_non_string_name(self):
        """Valida que el nombre de usuario sea una cadena válida."""
        credentials = {**self.credentials, "name": ["Ana"]}

        response = self.post_with_csrf(self.register_url, credentials)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_login_returns_tokens_for_valid_email_and_password(self):
        """El inicio de sesión exitoso configura las cookies JWT correspondientes."""
        self.post_with_csrf(self.register_url, self.credentials)
        response = self.post_with_csrf(
            self.login_url,
            {"email": self.credentials["email"], "password": self.credentials["password"]},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["name"], self.credentials["name"])
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)
        self.assertTrue(response.cookies["access_token"]["httponly"])
        self.assertTrue(response.cookies["refresh_token"]["httponly"])

    def test_login_rejects_invalid_credentials(self):
        """Rechaza inicios de sesión con credenciales erróneas devolviendo HTTP 401."""
        response = self.post_with_csrf(
            self.login_url,
            {"email": "nobody@example.com", "password": "TallerSeguro!2026"},
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_rate_limits_repeated_failed_attempts(self):
        """Aplica rate limiting bloqueando la IP ante reiterados intentos fallidos de login."""
        cache.clear()
        self.client.defaults["REMOTE_ADDR"] = "198.51.100.42"
        credentials = {
            "email": "nobody@example.com",
            "password": "TallerSeguro!2026",
        }

        for _ in range(5):
            response = self.post_with_csrf(self.login_url, credentials)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.post_with_csrf(self.login_url, credentials)

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_login_rate_throttle_resolves_configured_rate(self):
        """El throttle de login obtiene la tasa definida en settings."""
        throttle = LoginRateThrottle()
        rate = throttle.get_rate()
        self.assertIsNotNone(rate)
        self.assertIn("/minute", rate)

    def test_current_user_requires_a_valid_access_token(self):
        """El endpoint /api/auth/me/ deniega acceso anónimo."""
        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_current_user_is_resolved_from_the_http_only_access_cookie(self):
        """Resuelve correctamente los datos de la cuenta a partir de la cookie HttpOnly."""
        registration = self.post_with_csrf(self.register_url, self.credentials)
        self.client.cookies["access_token"] = registration.cookies[
            "access_token"
        ].value

        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {"name": self.credentials["name"], "email": self.credentials["email"]},
        )
        self.assertEqual(response["Cache-Control"], "no-store")

    def test_tampered_access_token_cookie_is_rejected(self):
        """Un token de acceso adulterado en la cookie es rechazado con HTTP 401."""
        self.client.cookies["access_token"] = "token.falso.y.manipulado"

        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_requires_a_valid_refresh_cookie(self):
        """El refresco de sesión falla si no se provee la cookie de refresco."""
        response = self.post_with_csrf("/api/auth/token/refresh/", {})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

    def test_refresh_rotates_jwt_cookies_without_returning_tokens(self):
        """La rotación de refresh emite nuevas cookies sin exponer el token en el cuerpo."""
        self.post_with_csrf(self.register_url, self.credentials)

        response = self.post_with_csrf("/api/auth/token/refresh/", {})

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertNotIn("access", response.data or {})
        self.assertNotIn("refresh", response.data or {})
        self.assertTrue(response.cookies["access_token"]["httponly"])
        self.assertTrue(response.cookies["refresh_token"]["httponly"])

    def test_refresh_token_reuse_is_prevented_after_rotation(self):
        """Impide el reúso de un refresh token previo luego de que ha sido rotado."""
        reg = self.post_with_csrf(self.register_url, self.credentials)
        initial_refresh = reg.cookies["refresh_token"].value

        # Primer refresco: rota el token
        rot_response = self.post_with_csrf("/api/auth/token/refresh/", {})
        self.assertEqual(rot_response.status_code, status.HTTP_204_NO_CONTENT)

        # Intento de reusar el refresh token inicial ya invalidado
        self.client.cookies["refresh_token"] = initial_refresh
        reuse_response = self.post_with_csrf("/api/auth/token/refresh/", {})
        self.assertEqual(reuse_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_revokes_and_clears_cookies_without_an_access_token(self):
        """El cierre de sesión invalida el refresh token en la base y expira las cookies."""
        registration = self.post_with_csrf(self.register_url, self.credentials)
        refresh_token = registration.cookies["refresh_token"].value
        self.client.cookies.pop("access_token", None)

        response = self.post_with_csrf("/api/auth/logout/", {})

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)
        self.assertEqual(response.cookies["access_token"]["max-age"], 0)
        self.assertEqual(response.cookies["refresh_token"]["max-age"], 0)
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertTrue(
            BlacklistedToken.objects.filter(token__token=refresh_token).exists()
        )

    def test_logout_without_cookies_responds_with_no_content(self):
        """El logout ejecutado sin cookies previas finaliza limpiamente con 204 No Content."""
        response = self.post_with_csrf("/api/auth/logout/", {})

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_login_rejects_requests_without_csrf_token(self):
        """Rechaza solicitudes POST si no envían el token CSRF obligatorio."""
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.get(self.csrf_url)

        response = self.client.post(
            self.login_url,
            {"email": self.credentials["email"], "password": self.credentials["password"]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
