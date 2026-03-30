from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.shortcuts import redirect
from django.contrib import messages
from .models import CustomUser

class OnlyExistingUsersAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing:
            return

        email = sociallogin.user.email
        if email:
            try:
                user = CustomUser.objects.get(email=email)
                sociallogin.connect(request, user)
            except CustomUser.DoesNotExist:
                messages.error(request, f"Обліковий запис з поштою {email} не знайдено.")
                raise ImmediateHttpResponse(redirect('login')) 
                
