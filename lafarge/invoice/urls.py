from django.urls import path

from . import views

urlpatterns = [
    path('salesmen/', views.salesman_list, name='salesman_list'),
    path('salesman/<int:salesman_id>/', views.salesman_detail, name='salesman_detail'),
    path('salesman/<int:salesman_id>/monthly-sales/', views.salesman_monthly_sales, name='salesman_monthly_sales'),
    path('customers/', views.CustomerListView.as_view(), name='customer_list'),
    path('customer/<str:customer_name>/', views.customer_detail, name='customer_detail'),
    path('products/', views.product_list, name='product_list'),
    path('products/<int:product_id>/', views.product_transaction_detail, name='product_transaction_detail'),
    path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
    path('invoice/<str:invoice_number>/', views.invoice_detail, name='invoice_detail'),
    path('delivery-note/<str:invoice_number>/download/', views.download_delivery_note_pdf,
         name='download_delivery_note_pdf'),
    path('invoice/legacy/<str:invoice_number>/download/', views.download_invoice_legacy_pdf,
         name='download_invoice_legacy_pdf'),
    path('invoice/<str:invoice_number>/download/', views.download_invoice_pdf, name='download_invoice_pdf'),
    path('orderform/<str:invoice_number>/download/', views.download_order_form_pdf, name='download_order_form_pdf'),
    path('sample/<str:invoice_number>/download/', views.download_sample_pdf, name='download_sample_pdf'),
    path('statement/<str:customer_name>/download/', views.download_statement_pdf, name='download_statement_pdf'),
    path("unpaid-invoices/", views.customers_with_unpaid_invoices, name="unpaid_invoices"),
    path("unpaid-invoices/<str:customer_name>/", views.unpaid_invoices_by_customer, name="customer_unpaid_invoices"),
    path("api/products/", views.ProductView, name="ProductView"),
    path("api/invoices/", views.InvoiceView, name="InvoiceView"),
    path("api/customers/", views.CustomerView, name="CustomerView"),
    path('', views.home, name='home'),
]
