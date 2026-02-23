from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django import forms

class RestrictDomainAdapter(DefaultAccountAdapter):
    def clean_email(self, email):
        email = super().clean_email(email)
        allowed_domain = '@upqroo.edu.mx'
        if not email.lower().endswith(allowed_domain):
            raise forms.ValidationError(
                f"Solo se permiten correos institucionales con el dominio {allowed_domain}."
            )
        return email

class RestrictSocialDomainAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        email = sociallogin.account.extra_data.get('email')
        if email:
            allowed_domain = '@upqroo.edu.mx'
            if not email.lower().endswith(allowed_domain):
                from django.contrib import messages
                messages.error(request, f"Solo se permiten correos institucionales con el dominio {allowed_domain}.")
                raise forms.ValidationError(f"Dominio no permitido: {email.split('@')[1]}")
        else:
            raise forms.ValidationError("No se pudo obtener el correo electrónico de Google.")
        return super().pre_social_login(request, sociallogin)