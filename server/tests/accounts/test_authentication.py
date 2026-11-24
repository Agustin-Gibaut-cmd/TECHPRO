"""Pruebas de integración para autenticación, cookies JWT y seguridad en accounts."""

from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

from accounts.throttling import LoginRateThrottle

User = get_user_model()


class AuthenticationApiTests(APITestCase):
    """Valida registro, inicio de sesión, rotación JWT, CSRF, rate limit y logout."""

    csrf_url = "/api/auth/csrf/"
    register_url = "/api/auth/register/"
    login_url = "/api/auth/login/"
    refresh_url = "/api/auth/token/refresh/"
    logout_url = "/api/auth/logout/"
    me_url = "/api/auth/me/"

    def setUp(self):
        """Prepara credenciales base y limpia la caché antes de cada prueba."""
        cache.clear()
        self.credentials = {
            "name": "Ana Pérez",
            "email": "ana@example.com",
            "password": "TallerSeguro!2026",
        }

    def _post_with_csrf(self, url: str, data: dict):
        """Solicita un token CSRF fresco y envía el POST correspondiente."""
        csrf_response = self.client.get(self.csrf_url)
        self.assertEqual(csrf_response["Cache-Control"], "no-store")
        return self.client.post(
            url,
            data,
            format="json",
            HTTP_X_CSRFTOKEN=csrf_response.data["csrfToken"],
        )

    def _register_and_get_cookies(self):
        """Registra el usuario base y retorna la respuesta con cookies JWT."""
        response = self._post_with_csrf(self.register_url, self.credentials)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response

    def test_registration_creates_user_and_sets_http_only_jwt_cookies(self):
        """Crea el usuario y emite cookies HttpOnly sin exponer tokens en el body."""
        response = self._post_with_csrf(self.register_url, self.credentials)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"]["email"], self.credentials["email"])
        self.assertEqual(response.data["user"]["name"], self.credentials["name"])
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
        """Rechaza registros con el mismo correo en distintas mayúsculas/minúsculas."""
        self._register_and_get_cookies()
        duplicate = {**self.credentials, "email": "ANA@example.com"}

        response = self._post_with_csrf(self.register_url, duplicate)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_registration_rejects_short_password(self):
        """Rechaza contraseñas por debajo de la longitud mínima."""
        response = self._post_with_csrf(
            self.register_url,
            {**self.credentials, "password": "short"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertFalse(User.objects.filter(email=self.credentials["email"]).exists())

    def test_registration_rejects_numeric_only_password(self):
        """Rechaza contraseñas compuestas solo por dígitos."""
        response = self._post_with_csrf(
            self.register_url,
            {**self.credentials, "password": "123456789012"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_registration_rejects_password_similar_to_email(self):
        """Rechaza contraseñas demasiado similares al correo del usuario."""
        response = self._post_with_csrf(
            self.register_url,
            {**self.credentials, "password": "ana_example_com_pass"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_registration_rejects_non_string_name(self):
        """Exige que el campo name sea un string válido."""
        response = self._post_with_csrf(
            self.register_url,
            {**self.credentials, "name": ["Ana"]},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_login_succeeds_with_valid_credentials_and_sets_cookies(self):
        """Autentica con credenciales válidas y establece las cookies JWT."""
        self._register_and_get_cookies()

        response = self._post_with_csrf(
            self.login_url,
            {
                "email": self.credentials["email"],
                "password": self.credentials["password"],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["name"], self.credentials["name"])
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)
        self.assertTrue(response.cookies["access_token"]["httponly"])
        self.assertTrue(response.cookies["refresh_token"]["httponly"])

    def test_login_rejects_invalid_credentials(self):
        """Devuelve 401 ante credenciales inexistentes o incorrectas."""
        response = self._post_with_csrf(
            self.login_url,
            {"email": "nobody@example.com", "password": "TallerSeguro!2026"},
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_rejects_inactive_user(self):
        """Impide el acceso a usuarios desactivados (is_active=False)."""
        self._register_and_get_cookies()
        user = User.objects.get(email=self.credentials["email"])
        user.is_active = False
        user.save(update_fields=["is_active"])

        response = self._post_with_csrf(
            self.login_url,
            {
                "email": self.credentials["email"],
                "password": self.credentials["password"],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_rate_limits_repeated_failed_attempts(self):
        """Bloquea por rate limit tras superar el máximo de intentos fallidos."""
        self.client.defaults["REMOTE_ADDR"] = "198.51.100.42"
        failed_payload = {
            "email": "nobody@example.com",
            "password": "TallerSeguro!2026",
        }

        for _ in range(5):
            response = self._post_with_csrf(self.login_url, failed_payload)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        blocked = self._post_with_csrf(self.login_url, failed_payload)
        self.assertEqual(blocked.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_login_rate_throttle_resolves_configured_rate(self):
        """Verifica que LoginRateThrottle devuelva una tasa válida en minutos."""
        rate = LoginRateThrottle().get_rate()
        self.assertIsNotNone(rate)
        self.assertIn("/minute", rate)

    def test_current_user_requires_authentication(self):
        """Rechaza el acceso anónimo a /api/auth/me/ con 401."""
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_current_user_resolves_from_http_only_access_cookie(self):
        """Retorna los datos públicos del usuario autenticado desde la cookie."""
        registration = self._register_and_get_cookies()
        self.client.cookies["access_token"] = registration.cookies["access_token"].value

        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "name": self.credentials["name"],
                "email": self.credentials["email"],
            },
        )
        self.assertEqual(response["Cache-Control"], "no-store")

    def test_tampered_access_token_cookie_is_rejected(self):
        """Rechaza un access_token inválido o manipulado con 401."""
        self.client.cookies["access_token"] = "token.falso.y.manipulado"

        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_requires_refresh_cookie(self):
        """Devuelve 401 si se intenta refrescar sin cookie refresh_token."""
        response = self._post_with_csrf(self.refresh_url, {})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

    def test_refresh_rotates_jwt_cookies_without_exposing_tokens(self):
        """Rota las cookies JWT y devuelve 204 sin tokens en el cuerpo."""
        self._register_and_get_cookies()

        response = self._post_with_csrf(self.refresh_url, {})

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertNotIn("access", response.data or {})
        self.assertNotIn("refresh", response.data or {})
        self.assertTrue(response.cookies["access_token"]["httponly"])
        self.assertTrue(response.cookies["refresh_token"]["httponly"])

    def test_refresh_token_reuse_is_rejected_after_rotation(self):
        """Impide reusar un refresh token ya rotado."""
        registration = self._register_and_get_cookies()
        initial_refresh = registration.cookies["refresh_token"].value

        rotated = self._post_with_csrf(self.refresh_url, {})
        self.assertEqual(rotated.status_code, status.HTTP_204_NO_CONTENT)

        self.client.cookies["refresh_token"] = initial_refresh
        reused = self._post_with_csrf(self.refresh_url, {})
        self.assertEqual(reused.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_revokes_refresh_token_and_expires_cookies(self):
        """Agrega el refresh token a la lista negra y expira las cookies de sesión."""
        registration = self._register_and_get_cookies()
        refresh_token = registration.cookies["refresh_token"].value
        self.client.cookies.pop("access_token", None)

        response = self._post_with_csrf(self.logout_url, {})

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.cookies["access_token"]["max-age"], 0)
        self.assertEqual(response.cookies["refresh_token"]["max-age"], 0)
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertTrue(
            BlacklistedToken.objects.filter(token__token=refresh_token).exists()
        )

    def test_logout_without_cookies_returns_204(self):
        """Responde 204 incluso si no hay cookies de sesión previas."""
        response = self._post_with_csrf(self.logout_url, {})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_login_rejects_requests_without_csrf_token(self):
        """Rechaza peticiones POST sin token CSRF válido con 403."""
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.get(self.csrf_url)

        response = self.client.post(
            self.login_url,
            {
                "email": self.credentials["email"],
                "password": self.credentials["password"],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)