# Generated by Django 5.1.6 on 2025-03-27 06:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("doc", "0021_alter_account_managed_groups"),
    ]

    operations = [
        migrations.AlterField(
            model_name="interviewinvitation",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="doc.account",
                verbose_name="Отправитель",
            ),
        ),
    ]
