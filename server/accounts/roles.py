"""Roles operativos y permisos basados en grupos de Django.

Los roles se asignan mediante grupos para no modificar el modelo de usuario:
- ``admin``: acceso completo.
- ``tecnico``: acceso completo a la operación del taller.
- ``vendedor``: acceso completo a la operación comercial.
- ``consulta``: solo lectura (GET, HEAD y OPTIONS).

Los usuarios sin grupo conservan acceso completo para no romper cuentas
existentes. Si una cuenta tiene ``consulta`` y además un rol operativo, prevalece
el rol operativo.
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission

ADMIN_ROLE = "admin"
TECHNICIAN_ROLE = "tecnico"
SALES_ROLE = "vendedor"
READ_ONLY_ROLE = "consulta"

WRITE_ROLES = frozenset({ADMIN_ROLE, TECHNICIAN_ROLE, SALES_ROLE})
ALL_ROLES = (ADMIN_ROLE, TECHNICIAN_ROLE, SALES_ROLE, READ_ONLY_ROLE)
ROLE_LABELS = {
    ADMIN_ROLE: "Administrador",
    TECHNICIAN_ROLE: "Técnico",
    SALES_ROLE: "Vendedor",
    READ_ONLY_ROLE: "Consulta",
}


def user_role_names(user) -> set[str]:
    """Retorna los nombres de los grupos asignados al usuario."""
    return set(user.groups.values_list("name", flat=True))


def is_read_only(user) -> bool:
    """Indica si la cuenta solo puede ejecutar métodos seguros."""
    roles = user_role_names(user)
    return READ_ONLY_ROLE in roles and not roles & WRITE_ROLES


class RoleAccessPermission(BasePermission):
    """Exige autenticación y bloquea escrituras al rol de consulta."""

    message = "Tu rol es de solo lectura."

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return not is_read_only(request.user)
