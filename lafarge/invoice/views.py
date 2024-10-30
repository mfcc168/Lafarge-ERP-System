import io

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from reportlab.lib.pagesizes import A4, A5
from reportlab.pdfgen import canvas

from .models import Customer, Invoice
from .models import Product, ProductTransaction
from .pdf_utils import draw_invoice_page, draw_order_form_page
from .tables import InvoiceTable, CustomerTable, InvoiceFilter, CustomerFilter, CustomerInvoiceTable, ProductTransactionTable, ProductTransactionFilter


class StaffMemberRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


@staff_member_required
def home(request):
    return render(request, 'invoice/home.html')


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
    transactions = ProductTransaction.objects.filter(product=product).order_by('-timestamp')

    # Apply filter
    filterset = ProductTransactionFilter(request.GET, queryset=transactions)
    table = ProductTransactionTable(filterset.qs)

    return render(request, 'invoice/product_transaction_detail.html', {
        'product': product,
        'transactions': filterset.qs,
        'table': table,
        'filter': filterset
    })
