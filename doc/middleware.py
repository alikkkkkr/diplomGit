from django.shortcuts import redirect
from django.urls import reverse


class AuthRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Список URL, которые доступны без авторизации
        allowed_urls = [
            reverse('authPage'),  # Страница авторизации
            reverse('regPage'),   # Страница регистрации
            reverse('organization_login'),  # Страница входа для организаций
            reverse('register_organization'),  # Страница регистрации организаций
        ]

        # Проверяем, авторизован ли пользователь
        if not request.session.get('email') and request.path not in allowed_urls:
            return redirect('authPage')  # Перенаправляем на страницу авторизации

        response = self.get_response(request)
        return response