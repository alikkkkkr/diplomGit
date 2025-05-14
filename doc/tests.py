from django.test import TestCase
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from .models import Account, Role, Intern, Organization, Group, Specialty, CollegeSupervisor
from .forms import UserRegisterForm, LoginForm, InternForm, OrganizationForm

class AccountModelTest(TestCase):
    def setUp(self):
        self.role = Role.objects.create(name='Студент')
        self.account = Account.objects.create(
            email='test@example.com',
            password=make_password('password'),
            surname='Иванов',
            name='Иван',
            role=self.role
        )

    def test_account_creation(self):
        self.assertEqual(self.account.email, 'test@example.com')
        self.assertEqual(self.account.surname, 'Иванов')
        self.assertTrue(self.account.check_password('password'))

    def test_account_str(self):
        self.assertEqual(str(self.account), 'Иванов Иван')

    def test_account_email_unique(self):
        with self.assertRaises(Exception):
            Account.objects.create(
                email='test@example.com',
                password='password',
                surname='Петров',
                name='Петр',
                role=self.role
            )

    def test_account_name_validation(self):
        account = Account(
            email='bad@example.com',
            password='password',
            surname='Иванов123',  # Невалидные символы
            name='Иван',
            role=self.role
        )
        with self.assertRaises(ValidationError):
            account.full_clean()

class RoleModelTest(TestCase):
    def setUp(self):
        self.role = Role.objects.create(name='Администратор')

    def test_role_creation(self):
        self.assertEqual(self.role.name, 'Администратор')

    def test_role_str(self):
        self.assertEqual(str(self.role), 'Администратор')

class InternModelTest(TestCase):
    def setUp(self):
        self.specialty = Specialty.objects.create(code="09.02.07", name="Программирование")
        self.group = Group.objects.create(name="П50", specialty=self.specialty)
        self.intern = Intern.objects.create(
            last_name='Петров',
            first_name='Петр',
            phone_number='+79991234567',
            group=self.group
        )

    def test_intern_creation(self):
        self.assertEqual(self.intern.last_name, 'Петров')
        self.assertEqual(self.intern.first_name, 'Петр')
        self.assertEqual(self.intern.group.name, 'П50')

    def test_intern_str(self):
        self.assertEqual(str(self.intern), 'Петров Петр - П50')

    def test_intern_optional_fields(self):
        intern = Intern.objects.create(
            last_name='Сидоров',
            first_name='Сергей',
            group=self.group
        )
        self.assertIsNone(intern.middle_name)
        self.assertIsNone(intern.email)

class GroupModelTest(TestCase):
    def setUp(self):
        self.specialty = Specialty.objects.create(code="09.02.07", name="Программирование")
        self.group = Group.objects.create(name="П50", specialty=self.specialty)

    def test_group_creation(self):
        self.assertEqual(self.group.name, 'П50')
        self.assertEqual(self.group.specialty.name, 'Программирование')

    def test_group_str(self):
        self.assertEqual(str(self.group), 'П50')

class SpecialtyModelTest(TestCase):
    def setUp(self):
        self.specialty = Specialty.objects.create(code="09.02.07", name="Программирование")

    def test_specialty_creation(self):
        self.assertEqual(self.specialty.code, '09.02.07')
        self.assertEqual(self.specialty.name, 'Программирование')

class OrganizationModelTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(
            full_name='Тестовая организация',
            email='org@example.com'
        )

    def test_organization_creation(self):
        self.assertEqual(self.org.full_name, 'Тестовая организация')
        self.assertEqual(self.org.is_approved, False)

    def test_organization_set_password(self):
        self.org.set_password('newpass')
        self.assertTrue(self.org.check_password('newpass'))

    def test_organization_str(self):
        self.assertEqual(str(self.org), 'Тестовая организация')

class CollegeSupervisorModelTest(TestCase):
    def setUp(self):
        self.supervisor = CollegeSupervisor.objects.create(
            last_name='Смирнов',
            first_name='Алексей',
            email='supervisor@example.com',
            position='Преподаватель'
        )

    def test_supervisor_creation(self):
        self.assertEqual(self.supervisor.last_name, 'Смирнов')
        self.assertEqual(self.supervisor.position, 'Преподаватель')

    def test_supervisor_str(self):
        self.assertEqual(str(self.supervisor), 'Смирнов Алексей')

class UserRegisterFormTest(TestCase):
    def test_valid_form(self):
        form_data = {
            'email': 'user@example.com',
            'password': 'TestPass123',
            'confirm_password': 'TestPass123',
            'surname': 'Иванов',
            'name': 'Иван'
        }
        form = UserRegisterForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_password_confirmation(self):
        form_data = {
            'email': 'user@example.com',
            'password': 'TestPass123',
            'confirm_password': 'WrongPass',
            'surname': 'Иванов',
            'name': 'Иван'
        }
        form = UserRegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Пароли не совпадают', str(form.errors))


class LoginFormTest(TestCase):
    def setUp(self):
        self.role = Role.objects.create(name='Студент')
        self.account = Account.objects.create(
            email='user@example.com',
            password=make_password('password'),
            surname='Иванов',
            name='Иван',
            role=self.role
        )

    def test_valid_login(self):
        form_data = {
            'email': 'user@example.com',
            'password': 'password'
        }
        form = LoginForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_login(self):
        form_data = {
            'email': 'user@example.com',
            'password': 'wrongpass'
        }
        form = LoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Неверный email или пароль', str(form.errors))

    def test_empty_email(self):
        form_data = {
            'email': '',
            'password': 'password'
        }
        form = LoginForm(data=form_data)
        self.assertFalse(form.is_valid())

class InternFormTest(TestCase):
    def setUp(self):
        self.specialty = Specialty.objects.create(code="09.02.07", name="Программирование")
        self.group = Group.objects.create(name="П50", specialty=self.specialty)

    def test_valid_intern_form(self):
        form_data = {
            'last_name': 'Петров',
            'first_name': 'Петр',
            'group': self.group.id
        }
        form = InternForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_intern_form(self):
        form_data = {
            'last_name': '',  # Пустая фамилия
            'first_name': 'Петр',
            'group': self.group.id
        }
        form = InternForm(data=form_data)
        self.assertFalse(form.is_valid())

class OrganizationFormTest(TestCase):
    def test_valid_organization_form(self):
        form_data = {
            'full_name': 'Новая организация',
            'email': 'new@org.com'
        }
        form = OrganizationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_organization_form(self):
        form_data = {
            'full_name': '',  # Пустое название
            'email': 'invalid-email'  # Невалидный email
        }
        form = OrganizationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)