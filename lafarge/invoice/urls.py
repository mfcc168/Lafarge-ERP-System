from django.urls import path

from .views.api_views import (
    ProductView, InvoiceView, CustomerView,
    UpdateDeliveryDateView, UpdatePaymentDateView
)
from .views.customer_page_views import (
    CustomerListView, customer_detail,
    customers_with_unpaid_invoices, unpaid_invoices_by_customer
)
from .views.home_page_views import home
from .views.invoice_page_views import InvoiceListView, invoice_detail
from .views.pdf_download_views import (
    download_delivery_note_pdf, download_invoice_legacy_pdf,
    download_invoice_pdf, download_order_form_pdf,
    download_sample_pdf, download_statement_pdf
)
from .views.salesman_page_views import (
    salesman_list, salesman_detail, salesman_monthly_sales
)
from .views.product_page_views import (
    product_list, product_transaction_detail
)

urlpatterns = [
    # Salesmen
    path('salesmen/', salesman_list, name='salesman_list'),
    path('salesman/<int:salesman_id>/', salesman_detail, name='salesman_detail'),
    path('salesman/<int:salesman_id>/monthly-sales/', salesman_monthly_sales, name='salesman_monthly_sales'),

    # Customers
    path('customers/', CustomerListView.as_view(), name='customer_list'),
    path('customer/<str:customer_name>/', customer_detail, name='customer_detail'),
    path('unpaid-invoices/', customers_with_unpaid_invoices, name='unpaid_invoices'),
    path('unpaid-invoices/<str:customer_name>/', unpaid_invoices_by_customer, name='customer_unpaid_invoices'),

    # Products
    path('products/', product_list, name='product_list'),
    path('products/<int:product_id>/', product_transaction_detail, name='product_transaction_detail'),

    # Invoices
    path('invoices/', InvoiceListView.as_view(), name='invoice_list'),
    path('invoice/<str:invoice_number>/', invoice_detail, name='invoice_detail'),

    # PDF Downloads
    path('delivery-note/<str:invoice_number>/download/', download_delivery_note_pdf, name='download_delivery_note_pdf'),
    path('invoice/legacy/<str:invoice_number>/download/', download_invoice_legacy_pdf, name='download_invoice_legacy_pdf'),
    path('invoice/<str:invoice_number>/download/', download_invoice_pdf, name='download_invoice_pdf'),
    path('orderform/<str:invoice_number>/download/', download_order_form_pdf, name='download_order_form_pdf'),
    path('sample/<str:invoice_number>/download/', download_sample_pdf, name='download_sample_pdf'),
    path('statement/<str:customer_name>/download/', download_statement_pdf, name='download_statement_pdf'),

    # API Endpoints
    path("api/products/", ProductView, name="ProductView"),
    path("api/invoices/", InvoiceView, name="InvoiceView"),
    path("api/customers/", CustomerView, name="CustomerView"),
    path('api/update-delivery-date/', UpdateDeliveryDateView.as_view(), name='update-delivery-date'),
    path('api/update-payment-date/', UpdatePaymentDateView.as_view(), name='update-payment-date'),

    # Home
    path('', home, name='home'),
]
