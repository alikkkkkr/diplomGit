from django import forms
from django.contrib.auth.hashers import make_password
from django.forms import inlineformset_factory
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


# Форма для модели Intern
class InternForm(forms.ModelForm):
    class Meta:
        model = Intern
        fields = ['last_name', 'first_name', 'middle_name', 'phone_number', 'metro_station', 'group',
                  'college_supervisor', 'organization']


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


# Форма для модели Schedule
class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['schedule_description']


# Форма для модели Practice
class PracticeForm(forms.ModelForm):
    class Meta:
        model = Practice
        fields = ['pp', 'pm', 'preddiplom', 'schedule', 'hours', 'group']


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
