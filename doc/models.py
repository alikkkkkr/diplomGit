import re
import uuid
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.crypto import get_random_string


class Role(models.Model):
    name = models.CharField(max_length=255, verbose_name='Роль')

    def __str__(self):
        return self.name


class DocumentLinks(models.Model):
    account = models.ForeignKey('Account', on_delete=models.CASCADE, related_name='document_links', verbose_name="Аккаунт")
    document_link = models.URLField(verbose_name="Ссылка на документ")

    def __str__(self):
        return self.document_link


class Account(models.Model):
    email = models.EmailField(unique=True, verbose_name="Электронная почта")
    password = models.CharField(max_length=255, verbose_name="Пароль")
    surname = models.CharField(max_length=50, verbose_name="Фамилия")
    name = models.CharField(max_length=50, verbose_name="Имя")
    patronymic = models.CharField(max_length=50, blank=True, null=True, verbose_name="Отчество")
    role = models.ForeignKey(Role, on_delete=models.PROTECT, verbose_name='Роль')

    def set_password(self, raw_password):
        self.salt_password = get_random_string(length=16)
        self.password = make_password(raw_password, salt=self.salt_password)

    def check_password(self, raw_password):
        def setter(raw_password):
            self.set_password(raw_password)
            self._password = raw_password
            self.save(update_fields=["password"])

        return check_password(raw_password, self.password, setter)

    def validate_name(self):
        if not re.match(r"^[A-Za-zА-Яа-яЁё]+$", self.surname) or not re.match(r"^[A-Za-zА-Яа-яЁё]+$", self.name):
            raise ValidationError("Фамилия и имя должны содержать только буквы")

    def clean(self):
        self.validate_name()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.surname} {self.name}"


class Tag(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название тега")

    def __str__(self):
        return self.name


class Intern(models.Model):
    last_name = models.CharField(max_length=50, verbose_name="Фамилия")
    first_name = models.CharField(max_length=50, verbose_name="Имя")
    middle_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="Отчество")
    phone_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Номер телефона")
    metro_station = models.CharField(max_length=50, blank=True, null=True, verbose_name="Ближайшее метро")
    group = models.ForeignKey('Group', on_delete=models.CASCADE, blank=True, null=True, verbose_name="Группа")
    college_supervisor = models.ForeignKey('CollegeSupervisor', on_delete=models.CASCADE, blank=True, null=True,
                                           verbose_name="Руководитель от техникума")
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE, blank=True, null=True, verbose_name="Организация")
    tags = models.ManyToManyField(Tag, blank=True, verbose_name="Теги")
    resume = models.FileField(upload_to='resumes/', blank=True, null=True, verbose_name="Резюме")
    # resume_access_granted = models.BooleanField(default=False, verbose_name="Доступ к резюме")

    # def validate_phone_number(self):
    #     if not re.match(r"^\+?[78]\d{10}$", self.phone_number):
    #         raise ValidationError("Неверный формат номера телефона. Используйте +7 или 8, затем 10 цифр.")

    # def clean(self):
    #     self.validate_phone_number()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def request_resume_access(self):
        if not self.resume_access_granted:
            self.resume_access_granted = True
            self.save()
            return True
        return False

    def __str__(self):
        return f"{self.last_name} {self.first_name} - {self.group.name}"


class Student(models.Model):
    account = models.OneToOneField(Account, on_delete=models.CASCADE, related_name='student', verbose_name="Аккаунт")
    is_intern = models.BooleanField(default=False, verbose_name="Практикант")

    def __str__(self):
        return f"Student: {self.account.surname} {self.account.name}"


class Group(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Название группы")
    specialty = models.ForeignKey('Specialty', on_delete=models.CASCADE, verbose_name="Специальность")

    def __str__(self):
        return self.name


class Schedule(models.Model):
    schedule_description = models.CharField(max_length=255, verbose_name="Описание графика")

    def __str__(self):
        return self.schedule_description


class Practice(models.Model):
    pp = models.CharField(max_length=100, verbose_name="Педагогическая практика", blank=True, null=True)
    pm = models.CharField(max_length=100, verbose_name="Производственная практика", blank=True, null=True)
    preddiplom = models.BooleanField(default=False, verbose_name="Преддипломная практика")
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, verbose_name="График практики")
    hours = models.PositiveIntegerField(verbose_name="Количество часов")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, verbose_name="Группа")

    def validate_practice_types(self):
        if self.preddiplom and (self.pp or self.pm):
            raise ValidationError("Невозможно установить преддипломную практику, если уже указаны ПП или ПМ.")

    def validate_positive_hours(self):
        if self.hours < 0:
            raise ValidationError("Количество часов не может быть отрицательным")

    def clean(self):
        self.validate_practice_types()
        self.validate_positive_hours()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.pp} {self.preddiplom} for {self.group.name}"


class CollegeSupervisor(models.Model):
    last_name = models.CharField(max_length=50, verbose_name="Фамилия")
    first_name = models.CharField(max_length=50, verbose_name="Имя")
    middle_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="Отчество")
    email = models.EmailField(verbose_name="Электронная почта")
    position = models.CharField(max_length=100, verbose_name="Должность")

    def validate_name(self):
        if not re.match(r"^[A-Za-zА-Яа-яЁё]+$", self.last_name) or not re.match(r"^[A-Za-zА-Яа-яЁё]+$", self.first_name):
            raise ValidationError("Фамилия и имя должны содержать только буквы")

    def clean(self):
        self.validate_name()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.last_name} {self.first_name}"


class Organization(models.Model):
    full_name = models.CharField(max_length=200, verbose_name="Полное наименование")
    legal_address = models.CharField(max_length=200, blank=True, null=True, verbose_name="Юридический адрес")
    actual_address = models.CharField(max_length=200, blank=True, null=True, verbose_name="Фактический адрес")
    inn = models.CharField(max_length=12, blank=True, null=True, verbose_name="ИНН")
    kpp = models.CharField(max_length=9, blank=True, null=True, verbose_name="КПП")
    ogrn = models.CharField(max_length=13, blank=True, null=True, verbose_name="ОГРН")
    phone_number = models.CharField(max_length=15, blank=True, null=True, verbose_name="Номер телефона")
    email = models.EmailField(blank=True, null=True,verbose_name="Электронная почта")
    is_approved = models.BooleanField(default=False, verbose_name="Подтверждено")
    password = models.CharField(max_length=128, verbose_name="Пароль", blank=True, null=True)
    is_registration_request = models.BooleanField(default=False, verbose_name="Заявка на регистрацию")

    # def validate_phone_number(self):
    #     if not re.match(r"^\+?[78]\d{10}$", self.phone_number):
    #         raise ValidationError("Неверный формат номера телефона. Используйте +7 или 8, затем 10 цифр.")

    # def validate_inn(self):
    #     if len(self.inn) != 12:
    #         raise ValidationError("ИНН должен состоять из 12 цифр")
    #
    # def validate_kpp(self):
    #     if len(self.kpp) != 9:
    #         raise ValidationError("КПП должен состоять из 9 цифр")
    #
    # def validate_ogrn(self):
    #     if len(self.ogrn) != 13:
    #         raise ValidationError("ОГРН должен состоять из 13 цифр")
    #
    # def clean(self):
    #     # self.validate_phone_number()
    #     self.validate_inn()
    #     self.validate_kpp()
    #     self.validate_ogrn()
    #
    # def save(self, *args, **kwargs):
    #     self.full_clean()
    #     super().save(*args, **kwargs)

    def set_password(self, raw_password):
        """Хеширует пароль и сохраняет его в поле password."""
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """Проверяет, совпадает ли переданный пароль с хешированным паролем."""
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.full_name


class Specialty(models.Model):
    code = models.CharField(max_length=20, verbose_name="Код специальности")
    name = models.CharField(max_length=255, verbose_name="Название специальности")

    def __str__(self):
        return self.code


class OrganizationSupervisor(models.Model):
    last_name = models.CharField(max_length=50, verbose_name="Фамилия")
    first_name = models.CharField(max_length=50, verbose_name="Имя")
    middle_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="Отчество")
    phone_number = models.CharField(max_length=15, verbose_name="Номер телефона")
    position = models.CharField(max_length=100, verbose_name="Должность")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, verbose_name="Организация")

    def validate_name(self):
        if not re.match(r"^[A-Za-zА-Яа-яЁё]+$", self.last_name) or not re.match(r"^[A-Za-zА-Яа-яЁё]+$", self.first_name):
            raise ValidationError("Фамилия и имя должны содержать только буквы")

    def validate_phone_number(self):
        if not re.match(r"^\+?[78]\d{10}$", self.phone_number):
            raise ValidationError("Неверный формат номера телефона. Используйте +7 или 8, затем 10 цифр.")

    def clean(self):
        self.validate_name()
        self.validate_phone_number()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.last_name} {self.first_name}"