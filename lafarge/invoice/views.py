from django.shortcuts import render, get_object_or_404
from .models import Customer, Invoice


from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io

from .pdf_utils import draw_invoice_page

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



def customer_list(request):
    # Get all customers along with their related invoices
    customers = Customer.objects.all().prefetch_related('invoice_set')

    # Pass the data to the template
    context = {
        'customers': customers,
    }
    return render(request, 'invoice/customer_list.html', context)