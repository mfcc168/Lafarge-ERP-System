from django.urls import path
from .views import invoice_detail, download_invoice_pdf

urlpatterns = [
    path('<str:invoice_number>', invoice_detail, name='invoice_detail'),
    path('<str:invoice_number>/download/', download_invoice_pdf, name='download_invoice_pdf'),
]
