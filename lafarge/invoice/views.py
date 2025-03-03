import io

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from django_tables2.config import RequestConfig
from django_tables2.export.export import TableExport
from reportlab.lib.pagesizes import A4, A5
from reportlab.pdfgen import canvas
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .pdf_generation.delivery_note import draw_delivery_note
from .pdf_generation.invoice import draw_invoice_page
from .pdf_generation.invoice_legacy import draw_invoice_page_legacy
from .pdf_generation.order_form import draw_order_form_page
from .pdf_generation.sample import draw_sample_page
from .pdf_generation.statement import draw_statement_page
from .serializers import *
from .tables import InvoiceTable, CustomerTable, InvoiceFilter, CustomerFilter, CustomerInvoiceTable, \
    ProductTransactionTable, ProductTransactionFilter, SalesmanInvoiceTable


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

    draw_invoice_page(pdf, invoice, "Poison Form")
    pdf.showPage()

    draw_invoice_page(pdf, invoice, "Original")
    pdf.showPage()

    draw_invoice_page(pdf, invoice, "Customer Copy")
    pdf.showPage()

    draw_invoice_page(pdf, invoice, "Company Copy")

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
def download_sample_pdf(request, invoice_number):
    # Get the invoice object
    sample = get_object_or_404(Invoice, number=invoice_number)

    # Create a buffer to hold the PDF data
    buffer = io.BytesIO()

    # Setup the canvas with the buffer as the file
    pdf = canvas.Canvas(buffer, pagesize=A5)

    # Draw the first page (Original copy)
    draw_sample_page(pdf, sample)

    # Save the PDF data to the buffer
    pdf.save()

    # Get the PDF content from the buffer
    buffer.seek(0)
    pdf_content = buffer.getvalue()
    buffer.close()

    # Create a response with PDF content
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Order_Form_{sample.number}.pdf"'

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
    products = Product.objects.all().order_by('name')
    return render(request, 'invoice/product_list.html', {'products': products})


@staff_member_required
def product_transaction_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    transactions = ProductTransaction.objects.filter(product=product).order_by('timestamp')

    # Apply filter
    filterset = ProductTransactionFilter(request.GET, queryset=transactions)
    table = ProductTransactionTable(filterset.qs)

    # Handle export
    export_format = request.GET.get("_export", None)
    if export_format:
        exporter = TableExport(export_format, table)
        return exporter.response(f"{product.name}_transactions.{export_format}")

    return render(request, 'invoice/product_transaction_detail.html', {
        'product': product,
        'transactions': filterset.qs,
        'table': table,
        'filter': filterset
    })


@staff_member_required
def customers_with_unpaid_invoices(request):
    # Fetch customers who have at least one unpaid invoice
    customers = Customer.objects.filter(invoice__payment_date__isnull=True).distinct().exclude(name="Sample")
    unpaid_invoices = Invoice.get_unpaid_invoices().exclude(number__startswith="S-")

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


@api_view(['GET'])
def ProductView(request):
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def InvoiceView(request):
    invoices = Invoice.objects.all()
    serializer = InvoiceSerializer(invoices, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def CustomerView(request):
    customers = Customer.objects.all()
    serializer = CustomerSerializer(customers, many=True)
    return Response(serializer.data)

class UpdateDeliveryDateView(APIView):
    def patch(self, request, *args, **kwargs):
        invoice_number = request.data.get('number')
        delivery_date = request.data.get('delivery_date')

        try:
            invoice = Invoice.objects.get(number=invoice_number)
        except Invoice.DoesNotExist:
            return Response({"error": "Invoice not found"}, status=status.HTTP_404_NOT_FOUND)

        # Update the delivery_date
        invoice.delivery_date = delivery_date
        invoice.save()

        # Serialize the updated invoice and return the response
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UpdatePaymentDateView(APIView):
    def patch(self, request, *args, **kwargs):
        invoice_number = request.data.get('number')
        payment_date = request.data.get('payment_date')

        try:
            invoice = Invoice.objects.get(number=invoice_number)
        except Invoice.DoesNotExist:
            return Response({"error": "Invoice not found"}, status=status.HTTP_404_NOT_FOUND)

        # Update the delivery_date
        invoice.payment_date = payment_date
        invoice.save()

        # Serialize the updated invoice and return the response
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data, status=status.HTTP_200_OK)
