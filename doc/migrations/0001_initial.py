# Generated by Django 5.1.6 on 2025-02-16 17:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Account",
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
                    "email",
                    models.EmailField(
                        max_length=254, unique=True, verbose_name="Электронная почта"
                    ),
                ),
                ("password", models.CharField(max_length=255, verbose_name="Пароль")),
                ("surname", models.CharField(max_length=50, verbose_name="Фамилия")),
                ("name", models.CharField(max_length=50, verbose_name="Имя")),
                (
                    "patronymic",
                    models.CharField(
                        blank=True, max_length=50, null=True, verbose_name="Отчество"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CollegeSupervisor",
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
                ("last_name", models.CharField(max_length=50, verbose_name="Фамилия")),
                ("first_name", models.CharField(max_length=50, verbose_name="Имя")),
                (
                    "middle_name",
                    models.CharField(
                        blank=True, max_length=50, null=True, verbose_name="Отчество"
                    ),
                ),
                (
                    "email",
                    models.EmailField(max_length=254, verbose_name="Электронная почта"),
                ),
                (
                    "position",
                    models.CharField(max_length=100, verbose_name="Должность"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Group",
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
                    "name",
                    models.CharField(
                        max_length=50, unique=True, verbose_name="Название группы"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Organization",
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
                    "full_name",
                    models.CharField(
                        max_length=200, verbose_name="Полное наименование"
                    ),
                ),
                (
                    "legal_address",
                    models.CharField(max_length=200, verbose_name="Юридический адрес"),
                ),
                (
                    "actual_address",
                    models.CharField(max_length=200, verbose_name="Фактический адрес"),
                ),
                ("inn", models.CharField(max_length=12, verbose_name="ИНН")),
                ("kpp", models.CharField(max_length=9, verbose_name="КПП")),
                ("ogrn", models.CharField(max_length=13, verbose_name="ОГРН")),
                (
                    "phone_number",
                    models.CharField(max_length=15, verbose_name="Номер телефона"),
                ),
                (
                    "email",
                    models.EmailField(max_length=254, verbose_name="Электронная почта"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Role",
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
                ("name", models.CharField(max_length=255, verbose_name="Роль")),
            ],
        ),
        migrations.CreateModel(
            name="Schedule",
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
                    "schedule_description",
                    models.CharField(max_length=255, verbose_name="Описание графика"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Specialty",
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
                    "code",
                    models.CharField(max_length=20, verbose_name="Код специальности"),
                ),
                (
                    "name",
                    models.CharField(
                        max_length=100, verbose_name="Название специальности"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="DocumentLinks",
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
                ("document_link", models.URLField(verbose_name="Ссылка на документ")),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="document_links",
                        to="doc.account",
                        verbose_name="Аккаунт",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Intern",
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
                ("last_name", models.CharField(max_length=50, verbose_name="Фамилия")),
                ("first_name", models.CharField(max_length=50, verbose_name="Имя")),
                (
                    "middle_name",
                    models.CharField(
                        blank=True, max_length=50, null=True, verbose_name="Отчество"
                    ),
                ),
                (
                    "phone_number",
                    models.CharField(
                        blank=True,
                        max_length=15,
                        null=True,
                        verbose_name="Номер телефона",
                    ),
                ),
                (
                    "metro_station",
                    models.CharField(
                        blank=True,
                        max_length=50,
                        null=True,
                        verbose_name="Ближайшее метро",
                    ),
                ),
                (
                    "college_supervisor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="doc.collegesupervisor",
                        verbose_name="Руководитель от техникума",
                    ),
                ),
                (
                    "group",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="doc.group",
                        verbose_name="Группа",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="doc.organization",
                        verbose_name="Организация",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="OrganizationSupervisor",
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
                ("last_name", models.CharField(max_length=50, verbose_name="Фамилия")),
                ("first_name", models.CharField(max_length=50, verbose_name="Имя")),
                (
                    "middle_name",
                    models.CharField(
                        blank=True, max_length=50, null=True, verbose_name="Отчество"
                    ),
                ),
                (
                    "phone_number",
                    models.CharField(max_length=15, verbose_name="Номер телефона"),
                ),
                (
                    "position",
                    models.CharField(max_length=100, verbose_name="Должность"),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="doc.organization",
                        verbose_name="Организация",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="account",
            name="role",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="doc.role",
                verbose_name="Роль",
            ),
        ),
        migrations.CreateModel(
            name="Practice",
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
                    "pp",
                    models.CharField(
                        blank=True,
                        max_length=100,
                        null=True,
                        verbose_name="Педагогическая практика",
                    ),
                ),
                (
                    "pm",
                    models.CharField(
                        blank=True,
                        max_length=100,
                        null=True,
                        verbose_name="Производственная практика",
                    ),
                ),
                (
                    "preddiplom",
                    models.BooleanField(
                        default=False, verbose_name="Преддипломная практика"
                    ),
                ),
                ("hours", models.PositiveIntegerField(verbose_name="Количество часов")),
                (
                    "group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="doc.group",
                        verbose_name="Группа",
                    ),
                ),
                (
                    "schedule",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="doc.schedule",
                        verbose_name="График практики",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="group",
            name="specialty",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="doc.specialty",
                verbose_name="Специальность",
            ),
        ),
        migrations.CreateModel(
            name="Student",
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
                    "is_intern",
                    models.BooleanField(default=False, verbose_name="Практикант"),
                ),
                (
                    "account",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="student",
                        to="doc.account",
                        verbose_name="Аккаунт",
                    ),
                ),
            ],
        ),
    ]
