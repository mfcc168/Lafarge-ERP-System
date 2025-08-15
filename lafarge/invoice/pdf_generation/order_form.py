import os
from datetime import datetime

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.platypus import Table, TableStyle

from ..check_utils import prefix_check


def draw_order_form_page(pdf, order):
    """
    Draw the content of an order form page in the PDF (A5 portrait).

    Args:
        pdf: The ReportLab Canvas object.
        order: The Order object.
    """
    width, height = A5

    # Draw the background image
    background_image_path = os.path.join(settings.STATIC_ROOT, 'OrderForm.png')
    pdf.drawImage(background_image_path, 0, 0, width, height)

    # Customer information
    pdf.setFont("Helvetica-Bold", 10)
    if order.customer.care_of:
        if prefix_check(order.customer.care_of.lower()):
            pdf.drawString(30, height - 100, f"From: {order.customer.care_of}")
        else:
            pdf.drawString(30, height - 100, f"From: Dr. {order.customer.care_of}")
    else:
        if prefix_check(order.customer.name.lower()):
            pdf.drawString(30, height - 100, f"From: {order.customer.name}")
        else:
            pdf.drawString(30, height - 100, f"From: Dr. {order.customer.name}")
    pdf.drawString(30, height - 120, f"To: LAFARGE CO., LTD.")
    pdf.drawString(30, height - 140, f"Date: {datetime.today().strftime('%Y-%b-%d')}")

    pdf.drawString(30, height - 180, "This is to place an order for the following medical product(s):")

    # Aggregate quantities for products with the same name but different units separately
    product_quantities = {}

    for item in order.invoiceitem_set.all():
        product_name = item.product.name.split('(')[0].strip()  # Strip lot no.
        key = (product_name, item.product.unit)  # Differentiate by unit

        if key in product_quantities:
            product_quantities[key] += item.quantity
        else:
            product_quantities[key] = item.quantity

    data = [["Product", "Quantity"]]
    for (product_name, unit), total_quantity in product_quantities.items():
        data.append([
            product_name,
            f"{float(total_quantity):,g} {unit}",  # Ensure correct unit is displayed
        ])

    table = Table(data, colWidths=[150, 50])
    table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
    ]))

    # Position the table to expand downward
    table.wrapOn(pdf, width, height)
    table_width, table_height = table.wrap(0, 0)  # Get actual table height
    table.drawOn(pdf, 110, height - 200 - table_height)  # Start lower for downward expansion

    # Footer
    if prefix_check(order.customer.name.lower()):
        pdf.drawString(30, height - 390, f"Please confirm by replying to {order.customer.name}")
    else:
        pdf.drawString(30, height - 390, f"Please confirm by replying to Dr. {order.customer.name}")
    pdf.drawString(30, height - 410, f"Tel:  {order.customer.telephone_number}")
