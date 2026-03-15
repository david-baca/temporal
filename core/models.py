
from django.db import models
from django.contrib.auth.models import User
import uuid  

class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    public_key = models.TextField(verbose_name="Clave pública (PEM)")
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"

class Documento(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documentos')
    titulo = models.CharField(max_length=255, blank=True, help_text="Título descriptivo del documento")
    archivo = models.FileField(upload_to='documentos/', verbose_name="Archivo PDF")
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo or 'Sin título'} - {self.uuid}"
    

class Firma(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='firmas')
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name='firmas')
    firma = models.TextField(verbose_name="Firma digital (hexadecimal)")
    fecha_firma = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'documento')  # Un usuario solo puede firmar un documento una vez

    def __str__(self):
        return f"Firma de {self.usuario.username} en {self.documento.uuid}"
  