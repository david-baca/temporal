from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Documento


class PasswordClaveForm(forms.Form):
    password = forms.CharField(
        label='Contraseña para proteger tu clave privada',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=8
    )
    confirm_password = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        pwd = cleaned_data.get('password')
        confirm = cleaned_data.get('confirm_password')
        if pwd and confirm and pwd != confirm:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data


class FirmaForm(forms.Form):
    documento_uuid = forms.UUIDField(label="UUID del documento", required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    clave_privada = forms.FileField(label="Archivo de clave privada (.key)", required=True, widget=forms.FileInput(attrs={'class': 'form-control'}))
    certificado = forms.FileField(label="Archivo de certificado (.cer)", required=True, widget=forms.FileInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Contraseña de la clave privada", required=True, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
        
    def clean_documento_uuid(self):
        uuid = self.cleaned_data['documento_uuid']
        try:
            documento = Documento.objects.get(uuid=uuid)
        except Documento.DoesNotExist:
            raise forms.ValidationError("No existe un documento con ese UUID.")
        return documento


class DocumentoForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields = ['titulo', 'archivo']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título del documento (opcional)'}),
            'archivo': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
        }

    def clean_archivo(self):
        archivo = self.cleaned_data['archivo']
        if not archivo.name.endswith('.pdf'):
            raise forms.ValidationError("Solo se permiten archivos PDF.")
        if archivo.size > 10 * 1024 * 1024:
            raise forms.ValidationError("El archivo no debe exceder los 10 MB.")
        return archivo
