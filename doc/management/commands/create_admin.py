from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from doc.models import Account, Role

# python manage.py create_admin


class Command(BaseCommand):
    help = 'Создает пользователя с ролью администратора'

    def handle(self, *args, **kwargs):
        # Проверяем, существует ли роль "Администратор"
        admin_role, created = Role.objects.get_or_create(name='Администратор')

        # info@technopromservice.ru

        # Создаем пользователя
        email = 'admin@example.com'
        password = 'adminpassword'  # Пароль для администратора
        hashed_password = make_password(password)

        user, created = Account.objects.get_or_create(
            email=email,
            defaults={
                'password': hashed_password,
                'surname': 'Admin',
                'name': 'User',
                'role': admin_role,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Пользователь {email} успешно создан.'))
        else:
            self.stdout.write(self.style.WARNING(f'Пользователь {email} уже существует.'))