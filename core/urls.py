from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('buscar/', views.buscar_documento, name='buscar_documento'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('documento/<uuid:uuid>/qr-pdf/', views.descargar_pdf_con_qr, name='descargar_pdf_con_qr'),
    path('establecer-password/', views.establecer_password_claves, name='establecer_password_claves'),
    path('post-login/', views.post_login_redirect, name='post_login_redirect'),
    path('descarga/', views.descarga_claves, name='descarga_claves'),
    path('descarga/privada/', views.descarga_privada, name='descarga_privada'),
    path('descarga/publica/', views.descarga_publica, name='descarga_publica'),
    path('firmar/', views.firmar_documento, name='firmar_documento'),
    path('subir/', views.subir_documento, name='subir_documento'),
    path('documento/<uuid:uuid>/', views.detalle_documento, name='detalle_documento'),
    path('documento/<uuid:uuid>/qr/', views.descargar_qr, name='descargar_qr'),
]