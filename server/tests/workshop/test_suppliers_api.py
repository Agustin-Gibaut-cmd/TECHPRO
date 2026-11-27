from typing import Any

from django.contrib.auth.models import AbstractBaseUser
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from tests.support import create_user, supplier_payload
from workshop.models import Supplier


class BaseSupplierApiTestCase(APITestCase):
    """Caso base con fixture autenticado y helpers compartidos para Supplier."""
    user: AbstractBaseUser
    default_payload: dict[str, Any]
    list_url: str

    def setUp(self) -> None:
        """Inicializa un usuario autenticado, payload base y URL de colección."""
        # Arrange
        self.user = create_user()
        self.client.force_authenticate(self.user)
        self.default_payload = supplier_payload()
        self.list_url = reverse("supplier-list-create")

    def build_detail_url(self, supplier_id: int) -> str:
        """Construye la URL del endpoint de detalle para un proveedor dado."""
        return reverse("supplier-detail", args=[supplier_id])

    def create_supplier_record(
        self,
        owner: AbstractBaseUser,
        **overrides: Any,
    ) -> Supplier:
        """Crea un proveedor en base de datos asignado a un propietario."""
        data: dict[str, Any] = {**self.default_payload, **overrides}
        return Supplier.objects.create(created_by=owner, **data)


class SupplierCrudAndIsolationTests(BaseSupplierApiTestCase):
    """Verifica operaciones CRUD y aislamiento de datos por propietario."""
    def test_supplier_crud_lifecycle_is_scoped_to_owner(self) -> None:
        """Valida creación (201), actualización parcial (200) y borrado (204)."""
        # Arrange
        updated_phone = "+54 11 5555-6666"
        # Act
        create_response = self.client.post(
            self.list_url,
            self.default_payload,
            format="json",
        )
        created_supplier = Supplier.objects.get(pk=create_response.data["id"])
        update_response = self.client.patch(
            self.build_detail_url(created_supplier.pk),
            {"phone": updated_phone},
            format="json",
        )
        created_supplier.refresh_from_db()
        delete_response = self.client.delete(self.build_detail_url(created_supplier.pk))
        # Assert
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(created_supplier.created_by, self.user)
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(created_supplier.phone, updated_phone)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Supplier.objects.filter(pk=created_supplier.pk).exists())

    def test_supplier_detail_is_not_visible_to_another_user(self) -> None:
        """Verifica que un proveedor de otro usuario no sea accesible (404)."""
        # Arrange
        other_user = create_user(email="otro@example.com")
        foreign_supplier = self.create_supplier_record(owner=other_user)
        # Act
        response = self.client.get(self.build_detail_url(foreign_supplier.pk))
        # Assert
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class SupplierValidationTests(BaseSupplierApiTestCase):
    """Verifica reglas de validación de datos al crear proveedores."""
    def test_supplier_create_rejects_invalid_email_format(self) -> None:
        """Rechaza un correo electrónico sin formato válido con estado 400."""
        # Arrange
        invalid_payload = supplier_payload(email="proveedor-sin-arroba")
        # Act
        response = self.client.post(self.list_url, invalid_payload, format="json")
        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_supplier_create_requires_name_and_phone(self) -> None:
        """Exige los campos obligatorios name y phone al crear un proveedor."""
        # Arrange
        incomplete_payload = {"email": "sin-datos@example.com"}

        # Act
        response = self.client.post(self.list_url, incomplete_payload, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)
        self.assertIn("phone", response.data)


class SupplierAuthenticationTests(BaseSupplierApiTestCase):
    """Verifica que los endpoints de proveedores exijan autenticación."""
    def test_supplier_endpoints_require_authentication(self) -> None:
        """Retorna 401 en colección y detalle cuando el cliente es anónimo."""
        # Arrange
        anonymous_client = APIClient()
        detail_url = self.build_detail_url(1)

        # Act
        list_response = anonymous_client.get(self.list_url)
        detail_response = anonymous_client.get(detail_url)

        # Assert
        self.assertEqual(list_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(detail_response.status_code, status.HTTP_401_UNAUTHORIZED)