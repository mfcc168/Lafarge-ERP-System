import io

from django.db.models import Q
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from reportlab.lib.pagesizes import A4, A5
from reportlab.pdfgen import canvas

from ..models import Invoice, Customer
from ..pdf_generation.delivery_note import draw_delivery_note
from ..pdf_generation.invoice import draw_invoice_page
from ..pdf_generation.invoice_legacy import draw_invoice_page_legacy
from ..pdf_generation.order_form import draw_order_form_page
from ..pdf_generation.sample import draw_sample_page
from ..pdf_generation.statement import draw_statement_page


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
    response['Content-Disposition'] = f'inline; filename="Invoice_Legacy_{invoice.number}.pdf"'

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
    response['Content-Disposition'] = f'inline; filename="Invoice_{invoice.number}.pdf"'

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
    response['Content-Disposition'] = f'inline; filename="Order_Form_{sample.number}.pdf"'

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
    response['Content-Disposition'] = f'inline; filename="Order_Form_{order_form.number}.pdf"'

    return response


@staff_member_required
def download_statement_pdf(request, customer_name, customer_care_of):
    # Get the invoice object
    customer = get_object_or_404(Customer, Q(name=customer_name) & (Q(care_of=customer_care_of) | Q(care_of__isnull=True)))
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
    response['Content-Disposition'] = f'inline; filename="Statement_{customer.name}.pdf"'

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
    response['Content-Disposition'] = f'inline; filename="Delivery_Note_{invoice.number}.pdf"'

    return response
