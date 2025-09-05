import os

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.platypus import Table, TableStyle

from ..check_utils import prefix_check


def draw_sample_page(pdf, invoice):
    """
    Draw the content of an order form page in the PDF (A5 portrait).

    Args:
        pdf: The ReportLab Canvas object.
        order: The Order object.
    """
    width, height = A5

    # Draw the background image
    background_image_path = os.path.join(settings.STATIC_ROOT, 'Sample.png')
    pdf.drawImage(background_image_path, 0, 0, width, height)

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(30, height - 53, f"Invoice No. : {invoice.number}")
    pdf.drawString(250, height - 120, f"Date: ")

    # Customer information
    address_lines = [line.strip() for line in invoice.customer.address.split("\n") if line.strip()]
    delivery_address_lines = [line.strip() for line in invoice.customer.delivery_address.split("\n") if line.strip()]
    office_hour_lines = [line.strip() for line in invoice.customer.office_hour.split("\n") if line.strip()]
    pdf.setFont("Helvetica-Bold", 10)
    if invoice.customer.name != "Sample":
        if prefix_check(invoice.customer.name.lower()):
            pdf.drawString(30, height - 120, f"TO: {invoice.customer.name}")
        else:
            pdf.drawString(30, height - 120, f"TO: Dr. {invoice.customer.name}")
        if invoice.customer.care_of:
            if prefix_check(invoice.customer.care_of.lower()):
                pdf.drawString(30, height - 130, f"{invoice.customer.care_of}")
            else:
                pdf.drawString(30, height - 130, f"C/O: Dr. {invoice.customer.care_of}")
        y_position = height - 150
        text_object = pdf.beginText(30, y_position)
        text_object.setFont("Helvetica", 10)
        for line in address_lines:
            text_object.textLine(line)

        text_object.textLine(
            f"Tel: {invoice.customer.telephone_number or ''}"
            f"{f' ({invoice.customer.contact_person})' if invoice.customer.contact_person else ''}"
        )

        pdf.drawText(text_object)

        if office_hour_lines:
            pdf.setFont("Helvetica-Bold", 8)
            pdf.drawString(300, height - 140, f"OFFICE HOURS:")
            text_object = pdf.beginText(300, height - 150)
            text_object.setFont("Helvetica", 8)
            for line in office_hour_lines:
                text_object.textLine(line)
            pdf.drawText(text_object)

    # Aggregate quantities for products with the same name
    product_quantities = {}
    for item in invoice.invoiceitem_set.all():
        product_name = item.product.name
        if product_name in product_quantities:
            product_quantities[product_name] += item.quantity
        else:
            product_quantities[product_name] = item.quantity

    data = [["Product", "Quantity"]]
    for product_name, total_quantity in product_quantities.items():
        data.append([
            product_name,
            f"{float(total_quantity):,g} {item.product.unit}",  # Use the unit from the last item processed
        ])

    table = Table(data, colWidths=[200, 50])
    table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
    ]))
    text_object = pdf.beginText(32, height - 410)
    if invoice.customer.show_delivery_address:
        for line in delivery_address_lines:
            text_object.textLine(line)
    pdf.drawText(text_object)
    # Position the table to expand downward
    table.wrapOn(pdf, width, height)
    table_width, table_height = table.wrap(0, 0)  # Get actual table height
    table.drawOn(pdf, 70, height - 200 - table_height)  # Start lower for downward expansion
