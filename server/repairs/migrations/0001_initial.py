"""Migración inicial: creación del modelo Repair y sus índices."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Repair",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("customer_name", models.CharField(max_length=120)),
                ("customer_phone", models.CharField(max_length=32)),
                ("device_type", models.CharField(max_length=80)),
                ("device_model", models.CharField(blank=True, max_length=100)),
                ("serial_number", models.CharField(blank=True, max_length=100)),
                ("issue_description", models.TextField(max_length=2000)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("received", "Recibido"),
                            ("diagnosing", "En diagnóstico"),
                            ("in_progress", "En reparación"),
                            ("waiting_parts", "Esperando repuesto"),
                            ("completed", "Listo"),
                            ("delivered", "Entregado"),
                        ],
                        default="received",
                        max_length=20,
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="repairs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ("-created_at", "-id"),
                "indexes": [
                    models.Index(
                        fields=["created_by", "-created_at"],
                        name="repairs_owner_created_idx",
                    ),
                ],
            },
        ),
    ]
