import os

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle

from ..check_utils import prefix_check


def draw_delivery_note(pdf, invoice):
    """
    Draw the content of an invoice page in the PDF.

    Args:
        pdf: The ReportLab Canvas object.
        invoice: The Invoice object.
    """
    width, height = A4

    background_image_path = os.path.join(settings.STATIC_ROOT, 'DeliveryNote.png')
    pdf.drawImage(background_image_path, 0, 0, width, height)

    # Customer information
    address_lines = [line.strip() for line in invoice.customer.delivery_address.split("\n") if line.strip()]
    pdf.setFont("Helvetica-Bold", 10)
    if prefix_check(invoice.customer.delivery_to.lower()):
        pdf.drawString(50, height - 180, f"Deliver To: {invoice.customer.delivery_to}")
    else:
        pdf.drawString(50, height - 180, f"Deliver To: Dr. {invoice.customer.delivery_to}")
    if invoice.customer.care_of:
        if prefix_check(invoice.customer.care_of.lower()):
            pdf.drawString(50, height - 190, f"C/O: {invoice.customer.care_of}")
        else:
            pdf.drawString(50, height - 190, f"C/O: Dr. {invoice.customer.care_of}")
    y_position = height - 200
    # Create a TextObject for multi-line address
    text_object = pdf.beginText(50, y_position)
    text_object.setFont("Helvetica", 9)
    for line in address_lines:
        text_object.textLine(line)

    text_object.textLine(
        f"Tel: {invoice.customer.telephone_number or ''}"
        f"{f' ({invoice.customer.contact_person})' if invoice.customer.contact_person else ''}"
    )
    pdf.drawText(text_object)

    pdf.setFont("Helvetica-Bold", 10)
    text_object = pdf.beginText(450, y_position)
    text_object.setFont("Helvetica", 10)

    if invoice.order_number:
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, height - 53, f"Order No. : {invoice.order_number}")

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, height - 296, f"Invoice No. : {invoice.number}")
    # Salesman and Date
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(50, height - 105, f"Date: ")

    # Define the data for the table
    data = [["Product", "Quantity"]]
    for item in invoice.invoiceitem_set.all():

        product_name = item.product.name
        product_name += f"\n"
        if invoice.customer.show_registration_code and item.product.registration_code:
            product_name += f"(Reg. No.: {item.product.registration_code})"
        if invoice.customer.show_expiry_date and item.product.expiry_date:
            product_name += f" (Exp.: {item.product.expiry_date.strftime('%Y-%b-%d')})"

        data.append([
            product_name,
            f"{float(item.quantity):g} {item.product.unit}\n",
        ])

    # Create the table
    table = Table(data, colWidths=[250, 150])
    table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
    ]))

    # Position the table
    table.wrapOn(pdf, width, height)
    table_width, table_height = table.wrap(0, 0)  # Get actual table height

    # Draw the table, positioning it to expand downward
    table.drawOn(pdf, 50, height - 306 - table_height)

    if prefix_check(invoice.customer.delivery_to.lower()):
        pdf.drawString(410, height - 670, f"{invoice.customer.delivery_to}")
    else:
        pdf.drawString(410, height - 670, f"{invoice.customer.delivery_to}")
