from django.shortcuts import render, get_object_or_404
from .models import Customer, Invoice
from .models import Product, ProductTransaction

from django_tables2 import SingleTableView, SingleTableMixin
from django_filters.views import FilterView
from .tables import InvoiceTable, InvoiceFilter

from django.http import HttpResponse
from reportlab.lib.pagesizes import A4, A5
from reportlab.pdfgen import canvas
import io

from .pdf_utils import draw_invoice_page, draw_order_form_page

def home(request):
    return render(request, 'invoice/home.html')

# def invoice_list(request):
#     invoices = Invoice.objects.all().order_by("-id")
#     return render(request, 'invoice/invoice_list.html', {'invoices': invoices})
class InvoiceListView(SingleTableMixin, FilterView):
    model = Invoice
    table_class = InvoiceTable
    template_name = "invoice/invoice_list.html"
    filterset_class = InvoiceFilter

def invoice_detail(request, invoice_number):
    # Fetch the invoice by its number
    invoice = get_object_or_404(Invoice, number=invoice_number)

    # Render the invoice template with the context
    context = {
        'invoice': invoice
    }
    return render(request, 'invoice/invoice_detail.html', context)




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


def customer_list(request):
    # Get all customers along with their related invoices
    customers = Customer.objects.all().prefetch_related('invoice_set')

    # Pass the data to the template
    context = {
        'customers': customers,
    }
    return render(request, 'invoice/customer_list.html', context)

def customer_detail(request, customer_name):
    # Fetch the customer by name, or return a 404 if not found
    customer = get_object_or_404(Customer, name=customer_name)

    # Pass the customer and related purchase records to the template
    context = {
        'customer': customer,
    }
    return render(request, 'invoice/customer_detail.html', context)

def product_list(request):
    products = Product.objects.all()
    return render(request, 'invoice/product_list.html', {'products': products})

def product_transaction_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    transactions = ProductTransaction.objects.filter(product=product).order_by('-timestamp')
    return render(request, 'invoice/product_transaction_detail.html', {
        'product': product,
        'transactions': transactions
    })