"""Migración de extensión: incorporación de los modelos Supplier y Sale."""

import django.core.validators
import django.db.models.deletion
from decimal import Decimal

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("workshop", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Supplier",
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
                ("name", models.CharField(max_length=120)),
                ("phone", models.CharField(max_length=32)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("address", models.CharField(blank=True, max_length=200)),
                ("notes", models.TextField(blank=True, max_length=1000)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="suppliers",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("name", "id"),
                "indexes": [
                    models.Index(
                        fields=["created_by", "name"],
                        name="supplier_owner_name_idx",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="Sale",
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
                ("customer_name", models.CharField(blank=True, max_length=120)),
                ("product_name", models.CharField(max_length=120)),
                ("quantity", models.PositiveIntegerField()),
                (
                    "unit_price",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        validators=[
                            django.core.validators.MinValueValidator(
                                Decimal("0.00")
                            )
                        ],
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sales",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("-created_at", "-id"),
                "indexes": [
                    models.Index(
                        fields=["created_by", "created_at"],
                        name="sale_owner_created_idx",
                    ),
                ],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("quantity__gt", 0)),
                        name="sale_quantity_positive",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("unit_price__gte", 0)),
                        name="sale_unit_price_nonnegative",
                    ),
                ],
            },
        ),
    ]
