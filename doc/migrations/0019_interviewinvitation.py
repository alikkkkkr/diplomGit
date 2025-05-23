# Generated by Django 5.1.6 on 2025-03-26 16:32

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("doc", "0018_alter_account_managed_groups"),
    ]

    operations = [
        migrations.CreateModel(
            name="InterviewInvitation",
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
                    "interview_date",
                    models.DateTimeField(verbose_name="Дата собеседования"),
                ),
                ("location", models.TextField(verbose_name="Место проведения")),
                (
                    "message",
                    models.TextField(
                        blank=True, verbose_name="Дополнительное сообщение"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Дата создания"
                    ),
                ),
                (
                    "is_accepted",
                    models.BooleanField(blank=True, null=True, verbose_name="Принято"),
                ),
                (
                    "response_date",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Дата ответа"
                    ),
                ),
                (
                    "intern",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="invitations",
                        to="doc.intern",
                    ),
                ),
            ],
            options={
                "verbose_name": "Приглашение на собеседование",
                "verbose_name_plural": "Приглашения на собеседование",
            },
        ),
    ]
