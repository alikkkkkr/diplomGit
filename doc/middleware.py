from django.shortcuts import redirect
from django.urls import reverse


class AuthRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        allowed_urls = [
            reverse('authPage'),
            reverse('regPage'),
            reverse('organization_login'),
            reverse('register_organization'),
        ]

        if not request.session.get('email') and request.path not in allowed_urls:
            return redirect('authPage')

        response = self.get_response(request)
        return response


