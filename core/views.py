from .utils import generar_overlay_qr, cargar_clave_publica, cargar_clave_privada, calcular_hash_pdf, firmar_hash, verificar_clave_privada_con_publica
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, FileResponse
from django.urls import reverse
from .forms import FirmaForm, PasswordClaveForm, DocumentoForm
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from .models import Documento, PerfilUsuario, Firma
from django.db.models import Q
from pypdf import PdfReader, PdfWriter
import qrcode
import os
from io import BytesIO


@login_required
def descargar_pdf_con_qr(request, uuid):
    documento = get_object_or_404(Documento, uuid=uuid)
    
    if not documento.archivo:
        messages.error(request, "El documento no tiene archivo asociado.")
        return redirect('detalle_documento', uuid=uuid)
    
    ruta_pdf = documento.archivo.path
    if not os.path.exists(ruta_pdf):
        messages.error(request, "El archivo PDF no se encuentra en el servidor.")
        return redirect('detalle_documento', uuid=uuid)

    # Obtener tamaño de la primera página
    reader_original = PdfReader(ruta_pdf)
    primera_pagina = reader_original.pages[0]
    ancho = float(primera_pagina.mediabox.width)
    alto = float(primera_pagina.mediabox.height)

    firmantes = [firma.usuario.get_full_name() or firma.usuario.username 
                 for firma in documento.firmas.all()]

    overlay_pdf = generar_overlay_qr(
        url=request.build_absolute_uri(reverse('detalle_documento', args=[documento.uuid])),
        firmantes=firmantes,
        page_width=ancho,
        page_height=alto
    )

    reader_overlay = PdfReader(overlay_pdf)
    writer = PdfWriter()

    # Aplicar overlay a cada página
    for page in reader_original.pages:
        page.merge_page(reader_overlay.pages[0])
        writer.add_page(page)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="documento_{documento.uuid}_con_qr.pdf"'
    writer.write(response)
    return response


def buscar_documento(request):
    uuid = request.GET.get('uuid')
    if uuid:
        try:
            documento = Documento.objects.get(uuid=uuid)
            return redirect('detalle_documento', uuid=documento.uuid)
        except Documento.DoesNotExist:
            messages.error(request, 'No existe un documento con ese UUID.')
    else:
        messages.error(request, 'Debe proporcionar un UUID.')
    return redirect('home')


@login_required
def dashboard(request):
    # Documentos donde el usuario ha participado (subidos o firmados)
    documentos = Documento.objects.filter(
        Q(usuario=request.user) | Q(firmas__usuario=request.user)
    ).distinct().order_by('-fecha_subida')
    
    return render(request, 'core/dashboard.html', {
        'documentos': documentos
    })



@login_required
def establecer_password_claves(request):
    if PerfilUsuario.objects.filter(user=request.user).exists():
        messages.info(request, "Ya tienes tus claves generadas.")
        return redirect('subir_documento')

    if request.method == 'POST':
        form = PasswordClaveForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password']

            private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            public_key = private_key.public_key()

            pem_public = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')

            PerfilUsuario.objects.create(user=request.user, public_key=pem_public)

            pem_private_encrypted = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.BestAvailableEncryption(password.encode('utf-8'))
            ).decode('utf-8')

            request.session['private_key_pem'] = pem_private_encrypted
            request.session['public_key_pem'] = pem_public

            return redirect('descarga_claves')
    else:
        form = PasswordClaveForm()

    return render(request, 'core/establecer_password.html', {'form': form})


@login_required
def post_login_redirect(request):
    if request.session.pop('nuevo_usuario_social', False):
        return redirect('establecer_password_claves')
    try:
        request.user.perfil
    except PerfilUsuario.DoesNotExist:
        return redirect('establecer_password_claves')
    return redirect('dashboard')


@login_required
def firmar_documento(request):
    if request.method == 'POST':
        form = FirmaForm(request.POST, request.FILES)
        if form.is_valid():
            documento = form.cleaned_data['documento_uuid']
            archivo_key = request.FILES['clave_privada']
            archivo_cert = request.FILES['certificado']
            password = form.cleaned_data['password']  # ahora obligatorio

            try:
                perfil = request.user.perfil
                public_key_pem = perfil.public_key
                public_key = cargar_clave_publica(public_key_pem)
            except PerfilUsuario.DoesNotExist:
                messages.error(request, "No tienes un perfil con clave pública.")
                return redirect('establecer_password_claves')

            try:
                private_key = cargar_clave_privada(archivo_key, password)
            except ValueError as e:
                messages.error(request, f"Error al cargar clave privada: {e}")
                return render(request, 'core/firmar_documento.html', {'form': form})

            if not verificar_clave_privada_con_publica(private_key, public_key):
                messages.error(request, "La clave privada no corresponde a tu usuario.")
                return render(request, 'core/firmar_documento.html', {'form': form})

            try:
                hash_doc = calcular_hash_pdf(documento.archivo)
            except Exception as e:
                messages.error(request, f"Error al calcular hash del PDF: {e}")
                return render(request, 'core/firmar_documento.html', {'form': form})

            try:
                firma_hex = firmar_hash(hash_doc, private_key)
            except Exception as e:
                messages.error(request, f"Error al firmar: {e}")
                return render(request, 'core/firmar_documento.html', {'form': form})

            firma, created = Firma.objects.get_or_create(
                usuario=request.user,
                documento=documento,
                defaults={'firma': firma_hex}
            )
            if not created:
                messages.warning(request, "Ya habías firmado este documento. Se ha actualizado la firma.")
                firma.firma = firma_hex
                firma.save()
            else:
                messages.success(request, "Documento firmado exitosamente.")

            return redirect('detalle_documento', uuid=documento.uuid)
    else:
        form = FirmaForm()

    return render(request, 'core/firmar_documento.html', {'form': form})


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')

@login_required
def subir_documento(request):
    """Vista para que usuarios autenticados suban un PDF."""
    if request.method == 'POST':
        form = DocumentoForm(request.POST, request.FILES)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.usuario = request.user
            documento.save()
            # Redirige a la página de detalle del documento
            return redirect('detalle_documento', uuid=documento.uuid)
    else:
        form = DocumentoForm()
    return render(request, 'core/subir_documento.html', {'form': form})


def detalle_documento(request, uuid):
    documento = get_object_or_404(Documento, uuid=uuid)
    firmas = documento.firmas.select_related('usuario').all()  # las firmas relacionadas
    url_consulta = request.build_absolute_uri(reverse('detalle_documento', args=[documento.uuid]))
    return render(request, 'core/detalle_documento.html', {
        'documento': documento,
        'firmas': firmas,
        'url_consulta': url_consulta,
    })


def descargar_qr(request, uuid):
    """Vista que genera y devuelve la imagen PNG del QR asociado al documento."""
    documento = get_object_or_404(Documento, uuid=uuid)
    url_consulta = request.build_absolute_uri(reverse('detalle_documento', args=[documento.uuid]))

    # Generar código QR
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url_consulta)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Guardar la imagen en un buffer
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    # Devolver como respuesta descargable
    response = HttpResponse(buffer, content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="qr_{documento.uuid}.png"'
    return response


@login_required
def descarga_privada(request):
    private_key_pem = request.session.get('private_key_pem')
    if not private_key_pem:
        return HttpResponse('No hay clave privada disponible', status=404)
    response = HttpResponse(private_key_pem, content_type='application/x-pem-file')
    response['Content-Disposition'] = 'attachment; filename="private.key"'
    # Eliminar de la sesión después de descargar (opcional, pero recomendado)
    del request.session['private_key_pem']
    return response


@login_required
def descarga_publica(request):
    public_key_pem = request.session.get('public_key_pem')
    if not public_key_pem:
        # Si no está en sesión, intentar obtener de la base de datos
        try:
            perfil = request.user.perfil
            public_key_pem = perfil.public_key
        except PerfilUsuario.DoesNotExist:
            return HttpResponse('No hay clave pública disponible', status=404)
    response = HttpResponse(public_key_pem, content_type='application/x-pem-file')
    response['Content-Disposition'] = 'attachment; filename="certificate.cer"'
    # Limpiar si estaba en sesión
    request.session.pop('public_key_pem', None)
    return response


@login_required
def descarga_claves(request):
    return render(request, 'core/descarga_claves.html')
