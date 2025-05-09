# Generated by Django 5.1.6 on 2025-04-25 14:28

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("doc", "0027_alter_specialty_organization"),
    ]

    operations = [
        migrations.CreateModel(
            name="DatabaseBackup",
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
                (
                    "file",
                    models.FileField(
                        upload_to="database_backups/", verbose_name="Файл бэкапа"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Дата создания"
                    ),
                ),
                ("size", models.CharField(max_length=20, verbose_name="Размер файла")),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="doc.account",
                        verbose_name="Создатель бэкапа",
                    ),
                ),
            ],
            options={
                "verbose_name": "Бэкап базы данных",
                "verbose_name_plural": "Бэкапы базы данных",
                "ordering": ["-created_at"],
            },
        ),
    ]
