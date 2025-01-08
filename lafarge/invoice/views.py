import io

from django.http import JsonResponse
from django.db.models import Sum
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from reportlab.lib.pagesizes import A4, A5
from reportlab.pdfgen import canvas

from .models import Customer, Invoice, Salesman
from .models import Product, ProductTransaction
from .pdf_utils import draw_invoice_page, draw_order_form_page, draw_statement_page, draw_delivery_note, draw_invoice_page_legacy
from .tables import InvoiceTable, CustomerTable, InvoiceFilter, CustomerFilter, CustomerInvoiceTable, ProductTransactionTable, ProductTransactionFilter, SalesmanInvoiceTable

from django_tables2.config import RequestConfig
from django_tables2.export.export import TableExport

from django.db.models.functions import TruncMonth
from django.db.models import Sum

class StaffMemberRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


@staff_member_required
def home(request):
    return render(request, 'invoice/home.html')

@staff_member_required
def salesman_list(request):
    salesmen = Salesman.objects.all()
    return render(request, 'invoice/salesman_list.html', {'salesmen': salesmen})

@staff_member_required
def salesman_detail(request, salesman_id):
    salesman = get_object_or_404(Salesman, id=salesman_id)
    invoices = Invoice.objects.filter(salesman=salesman)

    # Initialize filter with request data
    filter = InvoiceFilter(request.GET, queryset=invoices)
    filter.form.fields.pop('delivery_date', None)
    filter.form.fields.pop('delivery_date_to', None)
    filter.form.fields.pop('salesman', None)
    table = SalesmanInvoiceTable(filter.qs)  # Use filtered queryset

    # Handle export
    export_format = request.GET.get("_export", None)
    if export_format:
        exporter = TableExport(export_format, table)
        return exporter.response(f"{salesman.name}_invoices.{export_format}")

    return render(request, 'invoice/salesman_detail.html', {
        'salesman': salesman,
        'table': table,
        'filter': filter,
    })

def salesman_monthly_sales(request, salesman_id):
    # Get current year and start of each month in the year
    current_year = timezone.now().year
    monthly_sales = (
        Invoice.objects.filter(salesman_id=salesman_id, payment_date__year=current_year)
        .values('payment_date__month')  # Group by month
        .annotate(monthly_total=Sum('total_price'))  # Sum total_price per month
        .order_by('payment_date__month')
    )

    # Prepare data for the chart
    months = [0] * 12  # 12 months
    for sale in monthly_sales:
        month_index = sale['payment_date__month'] - 1
        months[month_index] = float(sale['monthly_total'] or 0)

    return JsonResponse({
        'months': ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        'sales': months,
    })

@method_decorator(staff_member_required, name='dispatch')
class InvoiceListView(StaffMemberRequiredMixin, SingleTableMixin, FilterView):
    model = Invoice
    table_class = InvoiceTable
    template_name = "invoice/invoice_list.html"
    filterset_class = InvoiceFilter


@staff_member_required
def invoice_detail(request, invoice_number):
    # Fetch the invoice by its number
    invoice = get_object_or_404(Invoice, number=invoice_number)

    # Render the invoice template with the context
    context = {
        'invoice': invoice
    }
    return render(request, 'invoice/invoice_detail.html', context)

@staff_member_required
def download_invoice_legacy_pdf(request, invoice_number):
    # Get the invoice object
    invoice = get_object_or_404(Invoice, number=invoice_number)

    # Create a buffer to hold the PDF data
    buffer = io.BytesIO()

    # Setup the canvas with the buffer as the file
    pdf = canvas.Canvas(buffer, pagesize=A4)

    draw_invoice_page_legacy(pdf, invoice)

    # Save the PDF data to the buffer
    pdf.save()

    # Get the PDF content from the buffer
    buffer.seek(0)
    pdf_content = buffer.getvalue()
    buffer.close()

    # Create a response with PDF content
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoice_Legacy_{invoice.number}.pdf"'

    return response

@staff_member_required
def download_invoice_pdf(request, invoice_number):
    # Get the invoice object
    invoice = get_object_or_404(Invoice, number=invoice_number)

    # Create a buffer to hold the PDF data
    buffer = io.BytesIO()

    # Setup the canvas with the buffer as the file
    pdf = canvas.Canvas(buffer, pagesize=A4)

    # Draw the first page (Original copy)
    draw_invoice_page(pdf, invoice, "Original")
    pdf.showPage()  # Start a new page

    # Draw the second page (Customer Copy)
    draw_invoice_page(pdf, invoice, "Customer Copy")
    pdf.showPage()  # Start a new page

    # Draw the third page (Company Copy)
    draw_invoice_page(pdf, invoice, "Company Copy")
    pdf.showPage()  # Start a new page

    # Draw the Forth page (Poison Form)
    draw_invoice_page(pdf, invoice, "Poison Form")

    # Save the PDF data to the buffer
    pdf.save()

    # Get the PDF content from the buffer
    buffer.seek(0)
    pdf_content = buffer.getvalue()
    buffer.close()

    # Create a response with PDF content
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoice_{invoice.number}.pdf"'

    return response


@staff_member_required
def download_order_form_pdf(request, invoice_number):
    # Get the invoice object
    order_form = get_object_or_404(Invoice, number=invoice_number)

    # Create a buffer to hold the PDF data
    buffer = io.BytesIO()

    # Setup the canvas with the buffer as the file
    pdf = canvas.Canvas(buffer, pagesize=A5)

    # Draw the first page (Original copy)
    draw_order_form_page(pdf, order_form)

    # Save the PDF data to the buffer
    pdf.save()

    # Get the PDF content from the buffer
    buffer.seek(0)
    pdf_content = buffer.getvalue()
    buffer.close()

    # Create a response with PDF content
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Order_Form_{order_form.number}.pdf"'

    return response


@method_decorator(staff_member_required, name='dispatch')
class CustomerListView(StaffMemberRequiredMixin, SingleTableMixin, FilterView):
    model = Customer
    table_class = CustomerTable
    template_name = "invoice/customer_list.html"
    filterset_class = CustomerFilter


@staff_member_required
def customer_detail(request, customer_name):
    customer = get_object_or_404(Customer, name=customer_name)
    invoices = Invoice.objects.filter(customer=customer)

    # Apply filter to the invoices queryset
    filterset = InvoiceFilter(request.GET, queryset=invoices)
    table = CustomerInvoiceTable(filterset.qs)
    RequestConfig(request).configure(table)

    # Check for export format in request and handle CSV export
    export_format = request.GET.get("_export", None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)  # Pass the table instance here
        return exporter.response(f"{customer_name}_invoices.{export_format}")

    context = {
        'customer': customer,
        'table': table,
        'filter': filterset,
    }
    return render(request, 'invoice/customer_detail.html', context)


@staff_member_required
def product_list(request):
    products = Product.objects.all()
    return render(request, 'invoice/product_list.html', {'products': products})


@staff_member_required
def product_transaction_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    transactions = ProductTransaction.objects.filter(product=product).order_by('timestamp')

    # Apply filter
    filterset = ProductTransactionFilter(request.GET, queryset=transactions)
    table = ProductTransactionTable(filterset.qs)

    return render(request, 'invoice/product_transaction_detail.html', {
        'product': product,
        'transactions': filterset.qs,
        'table': table,
        'filter': filterset
    })


@staff_member_required
def customers_with_unpaid_invoices(request):
    # Fetch customers who have at least one unpaid invoice
    customers = Customer.objects.filter(invoice__payment_date__isnull=True).distinct()
    unpaid_invoices = Invoice.get_unpaid_invoices()

    # Filter customer data to include only those with at least one unpaid invoice
    customer_data = [
        {
            "customer": customer,
            "unpaid_invoices": unpaid_invoices.filter(customer=customer),
        }
        for customer in customers
        if unpaid_invoices.filter(customer=customer).exists()  # Ensure at least one unpaid invoice
    ]

    # Calculate the total unpaid amount
    total_unpaid = Invoice.objects.filter(payment_date__isnull=True).aggregate(
        total=Sum('total_price')
    )['total'] or 0  # Default to 0 if no unpaid invoices

    # Calculate monthly unpaid totals
    monthly_unpaid = (
        Invoice.objects.filter(payment_date__isnull=True)
            .annotate(month=TruncMonth('delivery_date'))
            .values('month')
            .annotate(total=Sum('total_price'))
            .order_by('month')
    )

    context = {
        'customers': customers,
        'total_unpaid': total_unpaid,
        'monthly_unpaid': monthly_unpaid,
        'customer_data': customer_data,
    }
    return render(request, 'invoice/customers_with_unpaid_invoices.html', context)


@staff_member_required
def unpaid_invoices_by_customer(request, customer_name):
    customer = get_object_or_404(Customer, name=customer_name)
    unpaid_invoices = Invoice.get_unpaid_invoices().filter(customer=customer)



    return render(request, "invoice/unpaid_invoices_by_customer.html", {
        "customer": customer,
        "unpaid_invoices": unpaid_invoices,
    })

@staff_member_required
def download_statement_pdf(request, customer_name):
    # Get the invoice object
    customer = get_object_or_404(Customer, name=customer_name)
    unpaid_invoices = Invoice.get_unpaid_invoices().filter(customer=customer)

    # Create a buffer to hold the PDF data
    buffer = io.BytesIO()

    # Setup the canvas with the buffer as the file
    pdf = canvas.Canvas(buffer, pagesize=A4)

    # Draw the first page (Original copy)
    draw_statement_page(pdf, customer, unpaid_invoices)

    # Save the PDF data to the buffer
    pdf.save()

    # Get the PDF content from the buffer
    buffer.seek(0)
    pdf_content = buffer.getvalue()
    buffer.close()

    # Create a response with PDF content
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Statement_{customer.name}.pdf"'

    return response


@staff_member_required
def download_delivery_note_pdf(request, invoice_number):
    # Get the invoice object
    invoice = get_object_or_404(Invoice, number=invoice_number)

    # Create a buffer to hold the PDF data
    buffer = io.BytesIO()

    # Setup the canvas with the buffer as the file
    pdf = canvas.Canvas(buffer, pagesize=A4)

    # Draw the first page (Original copy)
    draw_delivery_note(pdf, invoice)

    # Save the PDF data to the buffer
    pdf.save()

    # Get the PDF content from the buffer
    buffer.seek(0)
    pdf_content = buffer.getvalue()
    buffer.close()

    # Create a response with PDF content
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Delivery_Note_{invoice.number}.pdf"'

    return response