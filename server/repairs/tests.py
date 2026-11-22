from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Repair

User = get_user_model()


class RepairApiTests(APITestCase):
    url = "/api/repairs/"

    def setUp(self):
        self.user = User.objects.create_user(
            username="ana@example.com",
            email="ana@example.com",
            password="TallerSeguro!2026",
        )
        self.client.force_authenticate(self.user)
        self.payload = {
            "customer_name": "Ana Pérez",
            "customer_phone": "+54 11 1234-5678",
            "device_type": "Notebook",
            "device_model": "ThinkPad T14",
            "serial_number": "SN-123456",
            "issue_description": "No enciende después de una caída.",
            "status": "diagnosing",
        }

    def test_authenticated_user_can_create_and_list_a_repair(self):
        create_response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_response.data["customer_name"], "Ana Pérez")
        self.assertEqual(create_response.data["status"], "diagnosing")
        self.assertEqual(Repair.objects.get().created_by, self.user)

        list_response = self.client.get(self.url)

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(list_response.data[0]["id"], create_response.data["id"])

    def test_user_cannot_list_repairs_created_by_another_user(self):
        other_user = User.objects.create_user(
            username="otro@example.com",
            email="otro@example.com",
            password="TallerSeguro!2026",
        )
        Repair.objects.create(created_by=other_user, **self.payload)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_repair_endpoints_require_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_status_is_rejected(self):
        response = self.client.post(
            self.url,
            {**self.payload, "status": "unknown"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", response.data)

    def test_owner_can_update_a_repair(self):
        repair = Repair.objects.create(created_by=self.user, **self.payload)

        response = self.client.patch(
            f"{self.url}{repair.pk}/",
            {"status": "completed", "issue_description": "Reparación finalizada."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        repair.refresh_from_db()
        self.assertEqual(repair.status, "completed")
        self.assertEqual(repair.issue_description, "Reparación finalizada.")

    def test_user_cannot_update_another_users_repair(self):
        other_user = User.objects.create_user(
            username="otro@example.com",
            email="otro@example.com",
            password="TallerSeguro!2026",
        )
        repair = Repair.objects.create(created_by=other_user, **self.payload)

        response = self.client.patch(
            f"{self.url}{repair.pk}/",
            {"status": "completed"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
