"""Base compartida para smoke tests de la API."""

import unittest

from .client import SmokeApiClient
from .constants import admin_email, api_url, read_only_email, test_password


class SmokeApiTestCase(unittest.TestCase):
    """Configura URL, credenciales y cliente HTTP para cada test."""

    api_url: str
    admin_email: str
    password: str
    read_only_email: str
    client: SmokeApiClient

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.api_url = api_url()
        cls.admin_email = admin_email()
        cls.password = test_password()
        cls.read_only_email = read_only_email()

    def setUp(self) -> None:
        self.client = SmokeApiClient(base_url=self.api_url)
