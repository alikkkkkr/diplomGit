import re
import logging
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


class Role(models.Model):
    name = models.CharField(max_length=255, verbose_name='Роль')

    def __str__(self):
        return self.name


class DocumentLinks(models.Model):
    account = models.ForeignKey('Account', on_delete=models.CASCADE, related_name='document_links',
                                verbose_name="Аккаунт")
    document_link = models.URLField(verbose_name="Ссылка на документ")

    def __str__(self):
        return self.document_link


class Document(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название документа")
    file = models.FileField(upload_to='documents/', verbose_name="Файл")
    practice = models.ForeignKey('Practice', on_delete=models.CASCADE, verbose_name="Практика", null=True, blank=True)
    uploaded_by = models.ForeignKey('Account', on_delete=models.CASCADE, verbose_name="Загружено")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")
    is_auto_fillable = models.BooleanField(default=False, verbose_name="Автозаполняемый")

    def __str__(self):
        return self.title


class Account(models.Model):
    email = models.EmailField(unique=True, verbose_name="Электронная почта")
    password = models.CharField(max_length=255, verbose_name="Пароль")
    surname = models.CharField(max_length=50, verbose_name="Фамилия")
    name = models.CharField(max_length=50, verbose_name="Имя")
    patronymic = models.CharField(max_length=50, blank=True, null=True, verbose_name="Отчество")
    role = models.ForeignKey(Role, on_delete=models.PROTECT, verbose_name='Роль')
    email_sent = models.BooleanField(default=False, verbose_name="Письмо отправлено")
    managed_groups = models.ManyToManyField('Group', blank=True, verbose_name="Управляемые группы")

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
        if not self.password:  # Если пароль не задан, создаем временный
            self.password = make_password('temporary_password')
        super().save(*args, **kwargs)

    def generate_and_send_password(self):
        if self.email_sent:
            logger.info(f"Письмо уже отправлено на {self.email}. Пропускаем.")
            return

        random_password = get_random_string(length=10)
        self.set_password(random_password)
        self.email_sent = True
        self.save()

        subject = 'Ваш пароль для входа на сайт'
        message = f'Ваш пароль для входа: {random_password}'
        from_email = settings.EMAIL_HOST_USER
        try:
            send_mail(
                subject,
                message,
                from_email,  # Указываем отправителя
                [self.email],  # Получатель
                fail_silently=False,
            )
            logger.info(f"Письмо с паролем отправлено на {self.email}")
        except Exception as e:
            logger.error(f"Ошибка при отправке письма: {e}")
            self.email_sent = False  # Если отправка не удалась, сбрасываем флаг
            self.save()

    @classmethod
    def send_passwords_to_all_students(cls):
        """
        Метод для отправки паролей на все почты студентов, где email_sent=False.
        """
        students = cls.objects.filter(role__name='Студент', email_sent=False)
        for student in students:
            student.generate_and_send_password()

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
    email = models.EmailField(unique=True, blank=True, null=True, verbose_name="Электронная почта")
    metro_station = models.CharField(max_length=50, blank=True, null=True, verbose_name="Ближайшее метро")
    group = models.ForeignKey('Group', on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Группа")
    college_supervisor = models.ForeignKey('CollegeSupervisor', on_delete=models.SET_NULL, blank=True, null=True,
                                           verbose_name="Руководитель от техникума")
    organization = models.ForeignKey('Organization', on_delete=models.SET_NULL, blank=True, null=True,
                                     verbose_name="Организация")
    tags = models.ManyToManyField(Tag, blank=True, verbose_name="Теги")
    resume = models.FileField(upload_to='resumes/', blank=True, null=True, verbose_name="Резюме")

    # resume_access_granted = models.BooleanField(default=False, verbose_name="Доступ к резюме")

    # def validate_phone_number(self):
    #     if not re.match(r"^\+?[78]\d{10}$", self.phone_number):
    #         raise ValidationError("Неверный формат номера телефона. Используйте +7 или 8, затем 10 цифр.")

    # def clean(self):
    #     self.validate_phone_number()

    @property
    def interview_invitations(self):
        return InterviewInvitation.objects.filter(intern=self).order_by('-created_at')

    def request_resume_access(self):
        if not self.resume:
            self.resume_access_granted = True
            self.save()
            return True
        return False

    def save(self, *args, **kwargs):
        # Если email был изменен
        if self.pk:
            old_intern = Intern.objects.get(pk=self.pk)
            if old_intern.email != self.email:
                # Обновляем связанный аккаунт
                account = Account.objects.filter(email=old_intern.email).first()
                if account:
                    account.email = self.email
                    account.save()

        super().save(*args, **kwargs)

        # # Если это существующий объект (редактирование)
        # if self.pk:
        #     old_intern = Intern.objects.get(pk=self.pk)
        #     # Если email был изменен
        #     if old_intern.email != self.email:
        #         # Удаляем старый аккаунт, если он существует
        #         Account.objects.filter(email=old_intern.email).delete()
        #
        # # Если email был изменен или добавлен
        # if self.email:
        #     if not self.pk:  # Проверяем, что это новый объект
        #         # Создаем аккаунт для студента
        #         account = Account.objects.create(
        #             email=self.email,
        #             surname=self.last_name,
        #             name=self.first_name,
        #             patronymic=self.middle_name,
        #             role=Role.objects.get(name='Студент'),
        #             password='temporary_password',  # Временный пароль
        #             email_sent=False  # Письмо еще не отправлено
        #         )
        #         account.generate_and_send_password()  # Генерация и отправка пароля
        #         Student.objects.create(account=account, is_intern=True)  # Создаем запись студента
        #     else:
        #         # Если это существующий объект, проверяем, изменился ли email
        #         old_intern = Intern.objects.get(pk=self.pk)
        #         if old_intern.email != self.email:
        #             # Обновляем email в аккаунте
        #             account = Account.objects.filter(email=old_intern.email).first()
        #             if account:
        #                 account.email = self.email
        #                 account.email_sent = False  # Сбрасываем флаг, так как email изменился
        #                 account.save()
        #                 account.generate_and_send_password()  # Генерация и отправка нового пароля
        #
        # super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.last_name} {self.first_name} - {self.group.name}"


class InterviewInvitation(models.Model):
    intern = models.ForeignKey(Intern, on_delete=models.CASCADE, related_name='invitations')
    interview_date = models.DateTimeField(verbose_name="Дата собеседования")
    location = models.TextField(verbose_name="Место проведения")
    message = models.TextField(blank=True, verbose_name="Дополнительное сообщение")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    is_accepted = models.BooleanField(null=True, blank=True, verbose_name="Принято")
    response_date = models.DateTimeField(null=True, blank=True, verbose_name="Дата ответа")
    created_by = models.ForeignKey(
        'Account',  # Изменено с User на Account
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Отправитель"
    )
    status_changed = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата изменения статуса"
    )

    def save(self, *args, **kwargs):
        # Обновляем дату изменения статуса при его изменении
        if self.pk and self.is_accepted != InterviewInvitation.objects.get(pk=self.pk).is_accepted:
            self.status_changed = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Приглашение для {self.intern} на {self.interview_date}"

    class Meta:
        verbose_name = "Приглашение на собеседование"
        verbose_name_plural = "Приглашения на собеседование"


class Student(models.Model):
    account = models.OneToOneField(Account, on_delete=models.CASCADE, related_name='student', verbose_name="Аккаунт")
    is_intern = models.BooleanField(default=False, verbose_name="Практикант")

    def __str__(self):
        return f"Student: {self.account.surname} {self.account.name}"


class Group(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Название группы")
    specialty = models.ForeignKey('Specialty', on_delete=models.PROTECT, verbose_name="Специальность")

    def __str__(self):
        return self.name


class Schedule(models.Model):
    schedule_description = models.CharField(max_length=255, verbose_name="Описание графика")

    def __str__(self):
        return self.schedule_description


class Practice(models.Model):
    pp = models.CharField(max_length=100, verbose_name="Производственная практика", blank=True, null=True)
    pm = models.CharField(max_length=100, verbose_name="Профессиональный модуль", blank=True, null=True)
    preddiplom = models.BooleanField(default=False, verbose_name="Преддипломная практика")
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, verbose_name="График практики")
    hours = models.PositiveIntegerField(verbose_name="Количество часов")
    groups = models.ManyToManyField(Group, verbose_name="Группы")

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
        return f"{self.pp} {self.preddiplom} for {self.groups.name}"


class CollegeSupervisor(models.Model):
    last_name = models.CharField(max_length=50, verbose_name="Фамилия")
    first_name = models.CharField(max_length=50, verbose_name="Имя")
    middle_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="Отчество")
    email = models.EmailField(verbose_name="Электронная почта")
    position = models.CharField(max_length=100, verbose_name="Должность")

    def validate_name(self):
        if not re.match(r"^[A-Za-zА-Яа-яЁё]+$", self.last_name) or not re.match(r"^[A-Za-zА-Яа-яЁё]+$",
                                                                                self.first_name):
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
    email = models.EmailField(blank=True, null=True, verbose_name="Электронная почта")
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


class Classification(models.Model):
    name = models.CharField(max_length=255, verbose_name="Классификация")

    def __str__(self):
        return self.name


class Specialty(models.Model):
    code = models.CharField(max_length=20, verbose_name="Код специальности")
    name = models.CharField(max_length=255, verbose_name="Специальность")
    organization = models.ForeignKey(Classification, blank=True, null=True, on_delete=models.CASCADE,
                                     verbose_name="Классификация")

    def __str__(self):
        return f"{self.code} - {self.organization.name}"


class OrganizationSupervisor(models.Model):
    last_name = models.CharField(max_length=50, verbose_name="Фамилия")
    first_name = models.CharField(max_length=50, verbose_name="Имя")
    middle_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="Отчество")
    phone_number = models.CharField(max_length=15, verbose_name="Номер телефона")
    position = models.CharField(max_length=100, verbose_name="Должность")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, verbose_name="Организация")

    def validate_name(self):
        if not re.match(r"^[A-Za-zА-Яа-яЁё]+$", self.last_name) or not re.match(r"^[A-Za-zА-Яа-яЁё]+$",
                                                                                self.first_name):
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


class DatabaseBackup(models.Model):
    file = models.FileField(upload_to='database_backups/', verbose_name="Файл бэкапа")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    size = models.CharField(max_length=20, verbose_name="Размер файла")
    created_by = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True,
                                  verbose_name="Создатель бэкапа")

    class Meta:
        verbose_name = "Бэкап базы данных"
        verbose_name_plural = "Бэкапы базы данных"
        ordering = ['-created_at']

    def __str__(self):
        return f"Бэкап от {self.created_at.strftime('%d.%m.%Y %H:%M')} ({self.size})"

    def save(self, *args, **kwargs):
        # Вычисляем размер файла перед сохранением
        if self.file:
            size_bytes = self.file.size
            if size_bytes < 1024:
                self.size = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                self.size = f"{size_bytes / 1024:.1f} KB"
            else:
                self.size = f"{size_bytes / (1024 * 1024):.1f} MB"
        super().save(*args, **kwargs)