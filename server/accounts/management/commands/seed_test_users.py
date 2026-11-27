"""Crea usuarios de prueba idempotentes para cada rol de TECHPRO."""

import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from accounts.roles import (
    ADMIN_ROLE,
    READ_ONLY_ROLE,
    ROLE_LABELS,
    SALES_ROLE,
    TECHNICIAN_ROLE,
)

User = get_user_model()

DEFAULT_PASSWORD = "TechproTest!2026"

TEST_USERS = (
    (ADMIN_ROLE, "admin@techpro.local", "Admin Techpro", True),
    (TECHNICIAN_ROLE, "tecnico@techpro.local", "Tecnico Techpro", False),
    (SALES_ROLE, "vendedor@techpro.local", "Vendedor Techpro", False),
    (READ_ONLY_ROLE, "consulta@techpro.local", "Consulta Techpro", False),
)


class Command(BaseCommand):
    """Crea o actualiza las cuentas de prueba y sus grupos de rol."""

    help = "Crea usuarios de prueba idempotentes para admin, tecnico, vendedor y consulta."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--password",
            default=os.getenv("TECHPRO_TEST_PASSWORD", DEFAULT_PASSWORD),
            help="Contraseña de las cuentas de prueba (por defecto TECHPRO_TEST_PASSWORD).",
        )
        parser.add_argument(
            "--reset-password",
            action="store_true",
            help="Restablece la contraseña de las cuentas existentes.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Permite ejecutar el comando con DEBUG=False.",
        )

    def handle(self, *args, **options) -> None:
        if not settings.DEBUG and not options["force"]:
            raise CommandError(
                "Este comando es solo para desarrollo. Usá --force para confirmar."
            )

        password = options["password"]
        for role, email, display_name, is_admin in TEST_USERS:
            group, _ = Group.objects.get_or_create(name=role)
            user, created = User.objects.get_or_create(
                username=email,
                defaults={"email": email, "first_name": display_name},
            )
            if created or options["reset_password"]:
                user.set_password(password)

            user.email = email
            user.first_name = display_name
            user.is_active = True
            user.is_staff = is_admin
            user.is_superuser = is_admin
            user.save()
            user.groups.add(group)

            state = "creado" if created else "actualizado"
            self.stdout.write(
                self.style.SUCCESS(
                    f"{ROLE_LABELS[role]}: {email} ({state})"
                )
            )
