from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature
from pypdf import PdfReader
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import letter

import qrcode


def generar_overlay_qr(url, firmantes, page_width, page_height):
    """
    Genera un PDF overlay con QR en la esquina inferior derecha,
    nombres de firmantes encima y leyenda en la izquierda.
    El tamaño del canvas se adapta a las dimensiones dadas.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

    # Generar imagen QR
    qr_img = qrcode.make(url)
    qr_path = BytesIO()
    qr_img.save(qr_path, format='PNG')
    qr_path.seek(0)

    # Tamaño del QR: máximo 60 puntos o 10% del lado menor
    qr_size = min(60, page_width * 0.1, page_height * 0.1)
    margin = 40
    qr_x = page_width - qr_size - margin
    qr_y = margin

    # Dibujar QR
    c.drawImage(ImageReader(qr_path), qr_x, qr_y, width=qr_size, height=qr_size)

    # Dibujar nombres de firmantes (justo encima del QR)
    if firmantes:
        c.setFont("Helvetica", 6)
        texto_firmantes = ", ".join(firmantes)
        text_width = c.stringWidth(texto_firmantes, "Helvetica", 6)
        x_text = qr_x + (qr_size - text_width) / 2
        y_text = qr_y + qr_size + 8
        c.drawString(x_text, y_text, texto_firmantes)

    # Leyenda de advertencia (esquina inferior izquierda)
    c.setFont("Helvetica", 7)
    leyenda = "Documento con QR estampado. Puede tapar información. Use el original para verificar."
    c.drawString(margin, margin, leyenda)

    c.save()
    buffer.seek(0)
    return buffer


def cargar_clave_publica(pem_public_key):
    """Carga una clave pública desde una cadena PEM."""
    return serialization.load_pem_public_key(
        pem_public_key.encode('utf-8'),
        backend=default_backend()
    )

def cargar_clave_privada(archivo_key, password=None):
    """
    Carga una clave privada desde un archivo (contenido en bytes).
    Si tiene contraseña, se proporciona como string.
    """
    try:
        if password:
            password = password.encode('utf-8')
        private_key = serialization.load_pem_private_key(
            archivo_key.read(),
            password=password,
            backend=default_backend()
        )
        return private_key
    except Exception as e:
        raise ValueError(f"Error al cargar la clave privada: {e}")

def calcular_hash_pdf(archivo_pdf):
    """
    Calcula el hash SHA-256 del contenido de un archivo PDF.
    El archivo_pdf puede ser un objeto File o una ruta.
    """
    import hashlib
    # Si es un archivo Django, necesitamos leerlo
    if hasattr(archivo_pdf, 'read'):
        # Leer todo el contenido y calcular hash
        contenido = archivo_pdf.read()
        archivo_pdf.seek(0)  # Reiniciar el puntero para futuras lecturas
        return hashlib.sha256(contenido).hexdigest()
    else:
        with open(archivo_pdf, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()

def firmar_hash(hash_hex, private_key):
    """
    Firma un hash (en hexadecimal) con la clave privada.
    Retorna la firma en hexadecimal.
    """
    hash_bytes = bytes.fromhex(hash_hex)
    signature = private_key.sign(
        hash_bytes,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    return signature.hex()

def verificar_clave_privada_con_publica(private_key, public_key):
    """
    Verifica que la clave privada corresponde a la pública firmando y verificando un mensaje de prueba.
    """
    mensaje_prueba = b"prueba de correspondencia"
    try:
        signature = private_key.sign(
            mensaje_prueba,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        public_key.verify(
            signature,
            mensaje_prueba,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return True
    except InvalidSignature:
        return False