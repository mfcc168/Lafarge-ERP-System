from django.urls import path
from .views import invoice_list, invoice_detail, download_invoice_pdf, customer_list, customer_detail\
    , product_list, product_transaction_detail\
    , home

urlpatterns = [
    path('customers/', customer_list, name='customer_list'),  # Added trailing slash for consistency
    path('customer/<str:customer_name>/', customer_detail, name='customer_detail'),
    path('products/', product_list, name='product_list'),
    path('products/<int:product_id>/', product_transaction_detail, name='product_transaction_detail'),
    path('invoices/', invoice_list, name='invoice_list'),
    path('invoice/<str:invoice_number>/', invoice_detail, name='invoice_detail'),  # Add prefix 'invoice/'
    path('invoice/<str:invoice_number>/download/', download_invoice_pdf, name='download_invoice_pdf'),  # Add prefix 'invoice/'
    path('', home, name='home'),
]

