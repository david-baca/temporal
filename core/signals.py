from django.dispatch import receiver
from allauth.socialaccount.signals import social_account_added
from django.shortcuts import redirect
from django.urls import reverse
from .models import PerfilUsuario
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


@receiver(social_account_added)
def nuevo_usuario_social(sender, request, sociallogin, **kwargs):
    user = sociallogin.user
    try:
        user.perfil
    except PerfilUsuario.DoesNotExist:
        request.session['nuevo_usuario_social'] = True
        request.session['nuevo_usuario_id'] = user.id
     