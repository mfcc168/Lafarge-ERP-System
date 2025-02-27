from decimal import Decimal, ROUND_UP
import os
from datetime import datetime

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, A5
from reportlab.platypus import Table, TableStyle
from reportlab.lib.utils import ImageReader

from ..encryption import encrypt_customer_id
from ..qrcode import generate_whatsapp_qr_code
from ..check_utils import prefix_check

def draw_statement_page(pdf, customer, unpaid_invoices):
    """
    Draw the content of an invoice page in the PDF.

    Args:
        pdf: The ReportLab Canvas object.
        invoice: The Invoice object.
    """
    width, height = A4

    # Draw the background image

    background_image_path = os.path.join(settings.STATIC_ROOT, 'Statement.png')
    pdf.drawImage(background_image_path, 0, 0, width, height)


    # Customer information
    address_lines = [line.strip() for line in customer.address.split("\n") if line.strip()]
    statement_use_additonal_lines = ""
    if customer.statement_use_additonal_line:
        statement_use_additonal_lines = [line.strip() for line in customer.statement_use_additonal_line.split("\n") if line.strip()]
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(50, height - 105, f"Date: {datetime.today().strftime('%Y-%b-%d')}")
    if prefix_check(customer.name.lower()):
        pdf.drawString(60, height - 180, f"{customer.name}")
    else:
        pdf.drawString(60, height - 180, f"Dr. {customer.name}")
    if customer.care_of:
        if prefix_check(customer.care_of.lower()):
            pdf.drawString(60, height - 200, f"C/O: {customer.care_of}")
        else:
            pdf.drawString(60, height - 200, f"C/O: Dr. {customer.care_of}")
    y_position = height - 220
    # Create a TextObject for multi-line address
    text_object = pdf.beginText(60, y_position)
    text_object.setFont("Helvetica", 10)
    for line in address_lines:
        text_object.textLine(line)
    for line in statement_use_additonal_lines:
        text_object.textLine(line)
    pdf.drawText(text_object)



    # Table for Invoice Items
    # Define the data for the table
    data = [["Invoice Date", "Invoice No.", "Amount"]]
    total_unpaid = 0
    for invoice in unpaid_invoices:
        total_unpaid += invoice.total_price
        data.append([
            invoice.delivery_date,
            invoice.number,
            f"HK$ {invoice.total_price:,.2f}"
        ])
    data.append([
        "",
        "",
        f"Total: HK$ {total_unpaid:,.2f}"
    ])

    # Create the table
    table = Table(data, colWidths=[100, 100, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgrey),  # Header background color
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),  # Header text color
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),  # Body background color
        ('GRID', (0, 0), (-1, -2), 0.5, colors.black),  # Border around cells
    ]))

    # Position the table
    table.wrapOn(pdf, width, height)
    table_width, table_height = table.wrap(0, 0)  # Get actual table height

    # Draw the table, positioning it to expand downward
    table.drawOn(pdf, 60, height - 366 - table_height)