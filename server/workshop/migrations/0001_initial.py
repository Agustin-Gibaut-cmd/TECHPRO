"""Migración inicial: creación de los modelos Customer e InventoryItem."""

import django.core.validators
import django.db.models.deletion
from decimal import Decimal

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Customer",
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
                        related_name="customers",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("name", "id"),
                "indexes": [
                    models.Index(
                        fields=["created_by", "name"],
                        name="customer_owner_name_idx",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="InventoryItem",
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
                ("sku", models.CharField(max_length=40)),
                ("category", models.CharField(blank=True, max_length=80)),
                ("description", models.TextField(blank=True, max_length=1000)),
                ("quantity", models.PositiveIntegerField(default=0)),
                ("min_stock", models.PositiveIntegerField(default=0)),
                (
                    "unit_price",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0.00"),
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
                        related_name="inventory_items",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("name", "id"),
                "indexes": [
                    models.Index(
                        fields=["created_by", "name"],
                        name="inventory_owner_name_idx",
                    ),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("created_by", "sku"),
                        name="inventory_owner_sku_unique",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("unit_price__gte", 0)),
                        name="inventory_unit_price_nonnegative",
                    ),
                ],
            },
        ),
    ]
