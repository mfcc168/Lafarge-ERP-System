from django.urls import path

from .views.api_views import (
    ProductView, InvoiceView, CustomerView,
    UpdateDeliveryDateView, UpdatePaymentDateView, SalesmanMonthlyReport, SalesmanMonthlyPreview
)
from .views.customer_page_views import (
    CustomerListView, customer_detail,
    customers_with_unpaid_invoices, unpaid_invoices_by_customer, unpaid_invoices_by_month_detail
)
from .views.home_page_views import home, sales_data, product_insights_data
from .views.invoice_page_views import InvoiceListView, invoice_detail, monthly_preview, monthly_report
from .views.pdf_download_views import (
    download_delivery_note_pdf, download_invoice_legacy_pdf,
    download_invoice_pdf, download_order_form_pdf,
    download_sample_pdf, download_statement_pdf
)
from .views.product_page_views import (
    product_list, product_transaction_detail, product_transaction_view
)
from .views.salesman_page_views import (
    salesman_list, SalesmanInvoiceView, salesman_monthly_sales, salesman_monthly_preview, salesman_monthly_report
)

from .views.payment_page_views import (monthly_payment_preview, monthly_payment_report)

urlpatterns = [
    # Salesmen
    path('salesmen/', salesman_list, name='salesman_list'),
    path('salesman/<int:salesman_id>/', SalesmanInvoiceView.as_view(), name='salesman_detail'),
    path('salesman/<int:salesman_id>/monthly-sales/', salesman_monthly_sales, name='salesman_monthly_sales'),
    path('salesman/<int:salesman_id>/monthly/', salesman_monthly_preview, name='salesman_monthly_preview'),
    path('salesman/<int:salesman_id>/monthly/<int:year>/<int:month>/', salesman_monthly_report, name='salesman_monthly_report'),

    # Customers
    path('customers/', CustomerListView.as_view(), name='customer_list'),
    path('customer/<str:customer_name>/<str:customer_care_of>/', customer_detail, name='customer_detail'),

    # Products
    path('products/', product_list, name='product_list'),
    path('products/<int:product_id>/', product_transaction_detail, name='product_transaction_detail'),
    path("product/<int:product_id>/transactions/", product_transaction_view, name="product_transactions"),

    # Invoices
    path('invoices/', InvoiceListView.as_view(), name='invoice_list'),
    path('invoice/<str:invoice_number>/', invoice_detail, name='invoice_detail'),

    # PDF Downloads
    path('delivery-note/<str:invoice_number>/download/', download_delivery_note_pdf, name='download_delivery_note_pdf'),
    path('invoice/legacy/<str:invoice_number>/download/', download_invoice_legacy_pdf, name='download_invoice_legacy_pdf'),
    path('invoice/<str:invoice_number>/download/', download_invoice_pdf, name='download_invoice_pdf'),
    path('orderform/<str:invoice_number>/download/', download_order_form_pdf, name='download_order_form_pdf'),
    path('sample/<str:invoice_number>/download/', download_sample_pdf, name='download_sample_pdf'),
    path('statement/<str:customer_name>/<str:customer_care_of>/download/', download_statement_pdf, name='download_statement_pdf'),

    # API Endpoints
    path("api/products/", ProductView, name="ProductView"),
    path("api/invoices/", InvoiceView, name="InvoiceView"),
    path("api/customers/", CustomerView, name="CustomerView"),
    path('api/update-delivery-date/', UpdateDeliveryDateView.as_view(), name='update-delivery-date'),
    path('api/update-payment-date/', UpdatePaymentDateView.as_view(), name='update-payment-date'),
    path('api/salesman/<int:salesman_id>/monthly/', SalesmanMonthlyReport.as_view(), name='salesman-monthly-preview'),
    path('api/salesman/<int:salesman_id>/monthly/<int:year>/<int:month>/', SalesmanMonthlyReport.as_view(), name='salesman-monthly-report'),

    # Payments
    path("payments/monthly", monthly_payment_preview, name="monthly_payment_preview"),
    path("payments/monthly/<int:year>/<int:month>/", monthly_payment_report, name="monthly_payment_report"),

    # Unpaids
    path('unpaid-invoices/', customers_with_unpaid_invoices, name='unpaid_invoices'),
    path('unpaid-invoices/<str:customer_name>/<str:customer_care_of>', unpaid_invoices_by_customer, name='customer_unpaid_invoices'),
    path('unpaid-invoices-by-month/<str:year_month>/', unpaid_invoices_by_month_detail, name='unpaid_invoices_by_month_detail'),

    # Sales
    path("invoices/monthly/", monthly_preview, name="monthly_preview"),
    path("invoices/monthly/<int:year>/<int:month>/", monthly_report, name="monthly_report"),

    # Home
    path('', home, name='home'),
    path('sales-data/', sales_data, name='sales_data'),
    path('product_insights/', product_insights_data, name='product_insights'),
]
