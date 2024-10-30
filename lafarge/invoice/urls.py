from django.urls import path

from .views import InvoiceListView, invoice_detail, download_invoice_pdf, download_order_form_pdf \
    , CustomerListView, customer_detail \
    , product_list, product_transaction_detail \
    , home

urlpatterns = [
    path('customers/', CustomerListView.as_view(), name='customer_list'),
    path('customer/<str:customer_name>/', customer_detail, name='customer_detail'),
    path('products/', product_list, name='product_list'),
    path('products/<int:product_id>/', product_transaction_detail, name='product_transaction_detail'),
    path('invoices/', InvoiceListView.as_view(), name='invoice_list'),
    path('invoice/<str:invoice_number>/', invoice_detail, name='invoice_detail'),
    path('invoice/<str:invoice_number>/download/', download_invoice_pdf, name='download_invoice_pdf'),
    path('orderform/<str:invoice_number>/download/', download_order_form_pdf, name='download_order_form_pdf'),
    path('', home, name='home'),
]
