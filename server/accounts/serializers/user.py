"""Serialización pública del usuario."""

from typing import Any


def serialize_user(user: Any) -> dict[str, str]:
    """Construye la representación pública del usuario."""
    return {
        "name": user.first_name or user.email,
        "email": user.email,
    }
