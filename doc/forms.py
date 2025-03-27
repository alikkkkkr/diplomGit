from django import forms
from django.contrib.auth.hashers import make_password
from django.forms import inlineformset_factory
from django.utils import timezone
from django.utils.crypto import get_random_string
from .models import *


# Форма регистрации пользователя
class UserRegisterForm(forms.ModelForm):
    # Добавляем поля для пароля и подтверждения пароля
    password = forms.CharField(
        widget=forms.PasswordInput,
        label='Пароль',
        help_text='Пароль должен содержать минимум 8 символов.'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
        label='Подтверждение пароля'
    )

    class Meta:
        model = Account
        fields = ['email', 'password', 'confirm_password', 'surname', 'name', 'patronymic']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        # Проверяем совпадение паролей
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Пароли не совпадают.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        # Генерация соли для хеширования пароля
        user.salt_password = get_random_string(length=16)
        # Хеширование пароля
        user.password = make_password(self.cleaned_data["password"], salt=user.salt_password)

        if commit:
            user.save()
        return user


# Форма авторизации пользователя
class LoginForm(forms.Form):
    email = forms.EmailField(label='Электронная почта')
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            try:
                user = Account.objects.get(email=email)
                if not user.check_password(password):
                    raise forms.ValidationError("Неверный email или пароль.")
            except Account.DoesNotExist:
                raise forms.ValidationError("Пользователь с таким email не найден.")
        return cleaned_data


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(label="Старый пароль", widget=forms.PasswordInput)
    new_password = forms.CharField(label="Новый пароль", widget=forms.PasswordInput)
    confirm_new_password = forms.CharField(label="Подтвердите новый пароль", widget=forms.PasswordInput)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        old_password = cleaned_data.get("old_password")
        new_password = cleaned_data.get("new_password")
        confirm_new_password = cleaned_data.get("confirm_new_password")

        if not self.user.check_password(old_password):
            raise ValidationError("Старый пароль введен неверно.")

        if new_password != confirm_new_password:
            raise ValidationError("Новый пароль и подтверждение не совпадают.")

        return cleaned_data


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'file', 'practice']


# Форма для модели Intern
class InternForm(forms.ModelForm):
    class Meta:
        model = Intern
        fields = ['last_name', 'first_name', 'middle_name', 'phone_number', 'email', 'metro_station', 'group',
                  'college_supervisor', 'organization']


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['email', 'surname', 'name', 'patronymic', 'role', 'managed_groups']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.role.name != 'Руководитель практики':
            self.fields['managed_groups'].widget = forms.HiddenInput()


# Форма для модели Student
class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['account', 'is_intern']


# Форма для модели Group
class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'specialty']


class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ['name']


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name']


# Форма для модели Schedule
class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['schedule_description']


# Форма для модели Practice
class PracticeForm(forms.ModelForm):
    class Meta:
        model = Practice
        fields = ['pp', 'pm', 'preddiplom', 'schedule', 'hours', 'groups']
        widgets = {
            'groups': forms.SelectMultiple(attrs={'class': 'form-control'}),  # Используем SelectMultiple
        }

    def clean(self):
        cleaned_data = super().clean()
        pp = cleaned_data.get("pp")
        pm = cleaned_data.get("pm")
        preddiplom = cleaned_data.get("preddiplom")

        if preddiplom and (pp or pm):
            raise forms.ValidationError("Невозможно установить преддипломную практику, если уже указаны ПП или ПМ.")

        if not preddiplom and not pp and not pm:
            raise forms.ValidationError("Необходимо заполнить либо ПП и ПМ, либо указать преддипломную практику.")

        return cleaned_data


# Форма для модели CollegeSupervisor
class CollegeSupervisorForm(forms.ModelForm):
    class Meta:
        model = CollegeSupervisor
        fields = ['last_name', 'first_name', 'middle_name', 'email', 'position']


# Форма для модели Organization
class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['full_name', 'legal_address', 'actual_address', 'inn', 'kpp', 'ogrn', 'phone_number', 'email']


class OrganizationRegistrationForm(forms.ModelForm):
    # Поля для организации
    password = forms.CharField(widget=forms.PasswordInput, label="Пароль")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Подтвердите пароль")

    # Поля для руководителя организации
    supervisor_last_name = forms.CharField(max_length=50, label="Фамилия руководителя")
    supervisor_first_name = forms.CharField(max_length=50, label="Имя руководителя")
    supervisor_middle_name = forms.CharField(max_length=50, label="Отчество руководителя", required=False)
    supervisor_phone_number = forms.CharField(max_length=15, label="Номер телефона руководителя")
    supervisor_position = forms.CharField(max_length=100, label="Должность руководителя")

    class Meta:
        model = Organization
        fields = [
            'full_name', 'legal_address', 'actual_address', 'inn', 'kpp', 'ogrn',
            'phone_number', 'email', 'password', 'confirm_password'
        ]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Пароли не совпадают.")

        return cleaned_data

    def save(self, commit=True):
        organization = super().save(commit=False)
        organization.set_password(self.cleaned_data["password"])
        organization.is_registration_request = True  # Устанавливаем флаг заявки на регистрацию

        if commit:
            organization.save()
            # Создаем руководителя организации
            supervisor = OrganizationSupervisor(
                last_name=self.cleaned_data["supervisor_last_name"],
                first_name=self.cleaned_data["supervisor_first_name"],
                middle_name=self.cleaned_data["supervisor_middle_name"],
                phone_number=self.cleaned_data["supervisor_phone_number"],
                position=self.cleaned_data["supervisor_position"],
                organization=organization
            )
            supervisor.save()

        return organization


class OrganizationLoginForm(forms.Form):
    email = forms.EmailField(label="Электронная почта")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        try:
            organization = Organization.objects.get(email=email)
            if not organization.check_password(password):
                raise forms.ValidationError("Неверный пароль.")
            if not organization.is_approved:
                raise forms.ValidationError("Организация не подтверждена.")
        except Organization.DoesNotExist:
            raise forms.ValidationError("Организация с таким email не найдена.")

        cleaned_data["organization"] = organization
        return cleaned_data


# Форма для модели Specialty
class SpecialtyForm(forms.ModelForm):
    class Meta:
        model = Specialty
        fields = ['code', 'name']


# Форма для модели OrganizationSupervisor
class OrganizationSupervisorForm(forms.ModelForm):
    class Meta:
        model = OrganizationSupervisor
        fields = ['last_name', 'first_name', 'middle_name', 'phone_number', 'position', 'organization']


# Форма для модели DocumentLinks
class DocumentLinksForm(forms.ModelForm):
    class Meta:
        model = DocumentLinks
        fields = ['document_link']


# InlineFormSet для связи Account с DocumentLinks
DocumentLinksFormSet = inlineformset_factory(
    Account,
    DocumentLinks,
    form=DocumentLinksForm,
    extra=1,
    can_delete=True
)


class StudentRegistrationForm(forms.ModelForm):
    class Meta:
        model = Intern
        fields = ['email']  # Используем поле email из модели Intern

    def save(self, commit=True):
        intern = super().save(commit=False)
        account = Account.objects.create(
            email=intern.email,
            surname=intern.last_name,
            name=intern.first_name,
            patronymic=intern.middle_name,
            role=Role.objects.get(name='Студент')
        )
        account.generate_and_send_password()  # Генерация и отправка пароля
        if commit:
            intern.save()
            Student.objects.create(account=account, is_intern=False)  # Создаем запись студента
        return account


class InterviewInvitationForm(forms.Form):
    interview_date = forms.DateTimeField(
        label="Дата и время собеседования",
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M']
    )
    location = forms.CharField(
        label="Место проведения",
        max_length=255,
        widget=forms.TextInput(attrs={'placeholder': 'Адрес или онлайн-платформа'})
    )
    message = forms.CharField(
        label="Дополнительное сообщение",
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Дополнительная информация...'})
    )

    def clean_interview_date(self):
        date = self.cleaned_data['interview_date']
        if date < timezone.now():
            raise forms.ValidationError("Дата собеседования не может быть в прошлом")
        return date
