from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

User = get_user_model()


class AuthenticationApiTests(APITestCase):
    csrf_url = "/api/auth/csrf/"
    register_url = "/api/auth/register/"
    login_url = "/api/auth/login/"

    def setUp(self):
        self.credentials = {
            "name": "Ana Pérez",
            "email": "ana@example.com",
            "password": "TallerSeguro!2026",
        }

    def post_with_csrf(self, url, data):
        csrf_response = self.client.get(self.csrf_url)
        self.assertEqual(csrf_response["Cache-Control"], "no-store")
        return self.client.post(
            url,
            data,
            format="json",
            HTTP_X_CSRFTOKEN=csrf_response.data["csrfToken"],
        )

    def test_registration_creates_user_and_sets_http_only_jwt_cookies(self):
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
        self.post_with_csrf(self.register_url, self.credentials)
        duplicate = {**self.credentials, "email": "ANA@example.com"}

        response = self.post_with_csrf(self.register_url, duplicate)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_registration_rejects_short_password(self):
        credentials = {**self.credentials, "password": "short"}

        response = self.post_with_csrf(self.register_url, credentials)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertFalse(User.objects.filter(email=self.credentials["email"]).exists())

    def test_registration_rejects_non_string_name(self):
        credentials = {**self.credentials, "name": ["Ana"]}

        response = self.post_with_csrf(self.register_url, credentials)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_login_returns_tokens_for_valid_email_and_password(self):
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
        response = self.post_with_csrf(
            self.login_url,
            {"email": "nobody@example.com", "password": "TallerSeguro!2026"},
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_current_user_requires_a_valid_access_token(self):
        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_current_user_is_resolved_from_the_http_only_access_cookie(self):
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

    def test_refresh_requires_a_valid_refresh_cookie(self):
        response = self.post_with_csrf("/api/auth/token/refresh/", {})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

    def test_refresh_rotates_jwt_cookies_without_returning_tokens(self):
        self.post_with_csrf(self.register_url, self.credentials)

        response = self.post_with_csrf("/api/auth/token/refresh/", {})

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertNotIn("access", response.data or {})
        self.assertNotIn("refresh", response.data or {})
        self.assertTrue(response.cookies["access_token"]["httponly"])
        self.assertTrue(response.cookies["refresh_token"]["httponly"])

    def test_logout_revokes_and_clears_cookies_without_an_access_token(self):
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

    def test_login_rejects_requests_without_csrf_token(self):
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.get(self.csrf_url)

        response = self.client.post(
            self.login_url,
            {"email": self.credentials["email"], "password": self.credentials["password"]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

