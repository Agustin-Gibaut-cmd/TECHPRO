"""Pruebas de integración para autenticación, cookies JWT y seguridad."""

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

from accounts.throttling import LoginRateThrottle

User = get_user_model()


class AuthenticationApiTests(APITestCase):
    """Valida registro, login, rotación JWT, CSRF, rate limit y logout."""

    def setUp(self):
        # Arrange
        cache.clear()
        self.csrf_url = reverse("csrf-token")
        self.register_url = reverse("register")
        self.login_url = reverse("login")
        self.refresh_url = reverse("token-refresh")
        self.logout_url = reverse("logout")
        self.me_url = reverse("current-user")
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
        # Act
        response = self._post_with_csrf(self.register_url, self.credentials)

        # Assert
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
        # Arrange
        self._register_and_get_cookies()
        duplicate = {**self.credentials, "email": "ANA@example.com"}

        # Act
        response = self._post_with_csrf(self.register_url, duplicate)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_registration_rejects_short_password(self):
        # Arrange
        payload = {**self.credentials, "password": "short"}

        # Act
        response = self._post_with_csrf(self.register_url, payload)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertFalse(User.objects.filter(email=self.credentials["email"]).exists())

    def test_registration_rejects_numeric_only_password(self):
        # Arrange
        payload = {**self.credentials, "password": "123456789012"}

        # Act
        response = self._post_with_csrf(self.register_url, payload)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_registration_rejects_password_similar_to_email(self):
        # Arrange
        payload = {**self.credentials, "password": "ana_example_com_pass"}

        # Act
        response = self._post_with_csrf(self.register_url, payload)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_registration_rejects_non_string_name(self):
        # Arrange
        payload = {**self.credentials, "name": ["Ana"]}

        # Act
        response = self._post_with_csrf(self.register_url, payload)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_login_succeeds_with_valid_credentials_and_sets_cookies(self):
        # Arrange
        self._register_and_get_cookies()
        payload = {
            "email": self.credentials["email"],
            "password": self.credentials["password"],
        }

        # Act
        response = self._post_with_csrf(self.login_url, payload)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["name"], self.credentials["name"])
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)
        self.assertTrue(response.cookies["access_token"]["httponly"])
        self.assertTrue(response.cookies["refresh_token"]["httponly"])

    def test_login_rejects_invalid_credentials(self):
        # Arrange
        payload = {"email": "nobody@example.com", "password": "TallerSeguro!2026"}

        # Act
        response = self._post_with_csrf(self.login_url, payload)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_rejects_inactive_user(self):
        # Arrange
        self._register_and_get_cookies()
        user = User.objects.get(email=self.credentials["email"])
        user.is_active = False
        user.save(update_fields=["is_active"])
        payload = {
            "email": self.credentials["email"],
            "password": self.credentials["password"],
        }

        # Act
        response = self._post_with_csrf(self.login_url, payload)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_rate_limits_repeated_failed_attempts(self):
        # Arrange
        self.client.defaults["REMOTE_ADDR"] = "198.51.100.42"
        failed_payload = {
            "email": "nobody@example.com",
            "password": "TallerSeguro!2026",
        }

        # Act
        responses = [
            self._post_with_csrf(self.login_url, failed_payload) for _ in range(6)
        ]

        # Assert
        for response in responses[:5]:
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(responses[-1].status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_login_rate_throttle_resolves_configured_rate(self):
        # Act
        rate = LoginRateThrottle().get_rate()

        # Assert
        self.assertIsNotNone(rate)
        self.assertIn("/minute", rate)

    def test_current_user_requires_authentication(self):
        # Act
        response = self.client.get(self.me_url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_current_user_resolves_from_http_only_access_cookie(self):
        # Arrange
        registration = self._register_and_get_cookies()
        self.client.cookies["access_token"] = registration.cookies["access_token"].value

        # Act
        response = self.client.get(self.me_url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {"name": self.credentials["name"], "email": self.credentials["email"]},
        )
        self.assertEqual(response["Cache-Control"], "no-store")

    def test_tampered_access_token_cookie_is_rejected(self):
        # Arrange
        self.client.cookies["access_token"] = "token.falso.y.manipulado"

        # Act
        response = self.client.get(self.me_url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_requires_refresh_cookie(self):
        # Act
        response = self._post_with_csrf(self.refresh_url, {})

        # Assert
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

    def test_refresh_rotates_jwt_cookies_without_exposing_tokens(self):
        # Arrange
        self._register_and_get_cookies()

        # Act
        response = self._post_with_csrf(self.refresh_url, {})

        # Assert
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertNotIn("access", response.data or {})
        self.assertNotIn("refresh", response.data or {})
        self.assertTrue(response.cookies["access_token"]["httponly"])
        self.assertTrue(response.cookies["refresh_token"]["httponly"])

    def test_refresh_token_reuse_is_rejected_after_rotation(self):
        # Arrange
        registration = self._register_and_get_cookies()
        initial_refresh = registration.cookies["refresh_token"].value

        # Act
        rotated = self._post_with_csrf(self.refresh_url, {})
        self.client.cookies["refresh_token"] = initial_refresh
        reused = self._post_with_csrf(self.refresh_url, {})

        # Assert
        self.assertEqual(rotated.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(reused.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_revokes_refresh_token_and_expires_cookies(self):
        # Arrange
        registration = self._register_and_get_cookies()
        refresh_token = registration.cookies["refresh_token"].value
        self.client.cookies.pop("access_token", None)

        # Act
        response = self._post_with_csrf(self.logout_url, {})

        # Assert
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.cookies["access_token"]["max-age"], 0)
        self.assertEqual(response.cookies["refresh_token"]["max-age"], 0)
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertTrue(
            BlacklistedToken.objects.filter(token__token=refresh_token).exists()
        )

    def test_logout_without_cookies_returns_204(self):
        # Act
        response = self._post_with_csrf(self.logout_url, {})

        # Assert
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_login_rejects_requests_without_csrf_token(self):
        # Arrange
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.get(self.csrf_url)
        payload = {
            "email": self.credentials["email"],
            "password": self.credentials["password"],
        }

        # Act
        response = self.client.post(self.login_url, payload, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
