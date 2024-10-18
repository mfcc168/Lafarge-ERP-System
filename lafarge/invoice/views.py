from django.shortcuts import render, get_object_or_404
from .models import Invoice

from django.conf import settings  # Add this import
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import io
import os

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
    width, height = A4

    # Draw the background image
    background_image_path = os.path.join(settings.STATIC_ROOT, 'Invoice.png')
    pdf.drawImage(background_image_path, 0, 0, width, height)

    # Set title font
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(450, height - 50, f"Original")

    # Customer information
    address_lines = [line.strip() for line in invoice.customer.address.split("\n") if line.strip()]  # Trim whitespace
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(70, height - 215, f"Sold To: {invoice.customer.name}")
    y_position = height - 230

    # Create a TextObject for multi-line address
    text_object = pdf.beginText(70, y_position)
    text_object.setFont("Helvetica", 10)

    for line in address_lines:
        text_object.textLine(line)

    pdf.drawText(text_object)

    # Salesman and Date
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(70, height - 110,
                   f"Date : {invoice.delivery_date.strftime('%Y-%m-%d') if invoice.delivery_date else ''}")
    pdf.drawString(70, height - 130,
                  f"Inovice No. : {invoice.number}")
    pdf.drawString(70, height - 150,
                  f"Terms : ")
    pdf.drawString(70, height - 170,
                  f"Salesman : {invoice.salesman.name}")

    # Table for Invoice Items
    data = [["Qty", "Product", "Unit Price", "Amount"]]
    for item in invoice.invoiceitem_set.all():
        data.append([
            item.quantity,
            item.product.name,
            f"${item.price:.2f}",
            f"${item.sum_price:.2f}"
        ])

    #data.append(["", "", "Subtotal", f"${invoice.total_price:.2f}"])

    # Configure table styles
    table = Table(data, colWidths=[50, 250, 100, 100])
    table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),

    ]))

    # Position the table
    table.wrapOn(pdf, width, height)
    table.drawOn(pdf, 50, height - 450)

    # Add total price at the bottom
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(400, height - 620, f"Total: ${invoice.total_price:.2f}")

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

