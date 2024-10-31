from django.urls import path

from . import views

urlpatterns = [
    path('salesmen/', views.salesman_list, name='salesman_list'),
    path('salesman/<int:salesman_id>/', views.salesman_detail, name='salesman_detail'),
    path('customers/', views.CustomerListView.as_view(), name='customer_list'),
    path('customer/<str:customer_name>/', views.customer_detail, name='customer_detail'),
    path('products/', views.product_list, name='product_list'),
    path('products/<int:product_id>/', views.product_transaction_detail, name='product_transaction_detail'),
    path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
    path('invoice/<str:invoice_number>/', views.invoice_detail, name='invoice_detail'),
    path('invoice/<str:invoice_number>/download/', views.download_invoice_pdf, name='download_invoice_pdf'),
    path('orderform/<str:invoice_number>/download/', views.download_order_form_pdf, name='download_order_form_pdf'),
    path('', views.home, name='home'),
]
