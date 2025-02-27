import os
from decimal import Decimal, ROUND_UP

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Table, TableStyle

from ..check_utils import prefix_check
from ..encryption import encrypt_customer_id
from ..qrcode import generate_whatsapp_qr_code


def draw_invoice_page(pdf, invoice, copy_type):
    """
    Draw the content of an invoice page in the PDF.

    Args:
        pdf: The ReportLab Canvas object.
        invoice: The Invoice object.
        copy_type: A string indicating the type of copy (e.g., "Original", "Customer Copy", "Company Copy", "Poison Form").
    """
    width, height = A4

    # Draw the background image
    if copy_type == "Poison Form":
        background_image_path = os.path.join(settings.STATIC_ROOT, 'PoisonForm.png')
    elif copy_type == "Customer Copy":
        background_image_path = os.path.join(settings.STATIC_ROOT, 'CustomerCopy.png')
    elif copy_type == "Company Copy":
        background_image_path = os.path.join(settings.STATIC_ROOT, 'CompanyCopy.png')
    else:
        background_image_path = os.path.join(settings.STATIC_ROOT, 'Invoice.png')
    pdf.drawImage(background_image_path, 0, 0, width, height)
    pdf.setFont("Helvetica-Bold", 12)

    # Customer information
    address_lines = [line.strip() for line in invoice.customer.address.split("\n") if line.strip()]
    delivery_address_lines = [line.strip() for line in invoice.customer.delivery_address.split("\n") if line.strip()]
    office_hour_lines = [line.strip() for line in invoice.customer.office_hour.split("\n") if line.strip()]
    pdf.setFont("Helvetica-Bold", 10)
    if prefix_check(invoice.customer.name.lower()):
        pdf.drawString(50, height - 165, f"SOLD TO: {invoice.customer.name}")
    else:
        pdf.drawString(50, height - 165, f"SOLD TO: Dr. {invoice.customer.name}")
    if invoice.customer.care_of and not invoice.customer.hide_care_of:
        if prefix_check(invoice.customer.care_of.lower()):
            pdf.drawString(50, height - 185, f"{invoice.customer.care_of}")
        else:
            pdf.drawString(50, height - 185, f"C/O: Dr. {invoice.customer.care_of}")
    y_position = height - 205
    # Create a TextObject for multi-line address
    text_object = pdf.beginText(50, y_position)
    text_object.setFont("Helvetica", 10)
    for line in address_lines:
        text_object.textLine(line)

    text_object.textLine(
        f"Tel: {invoice.customer.telephone_number or ''}"
        f"{f' ({invoice.customer.contact_person})' if invoice.customer.contact_person else ''}"
    )
    if invoice.order_number:
        text_object.textLine(f"Order No.: {invoice.order_number}")
    if invoice.customer.delivery_to:
        text_object.textLine(f"Deliver To: {invoice.customer.delivery_to}")
    if invoice.customer.show_delivery_address:
        for line in delivery_address_lines:
            text_object.textLine(line)

    pdf.drawText(text_object)

    if office_hour_lines:
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(450, height - 185, f"OFFICE HOURS:")
        text_object = pdf.beginText(450, y_position)
        text_object.setFont("Helvetica", 10)
        for line in office_hour_lines:
            text_object.textLine(line)
        pdf.drawText(text_object)

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, height - 53, f"Invoice No. : {invoice.number}")
    # Salesman and Date
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(50, height - 73, f"Date : ")
    pdf.drawString(50, height - 93, f"Salesman : {invoice.salesman.code}")
    if copy_type != "Poison Form":
        pdf.drawString(50, height - 113, f"Terms : {invoice.terms}")

    # Table for Invoice Items
    if copy_type == "Poison Form":
        # Aggregate quantities for products with the same name
        product_quantities = {}
        for item in invoice.invoiceitem_set.all():
            product_name = item.product.name
            if product_name in product_quantities:
                product_quantities[product_name] += item.quantity
            else:
                product_quantities[product_name] = item.quantity

        # Prepare table data
        data = [["Product", "Quantity"]]
        for product_name, total_quantity in product_quantities.items():
            data.append([
                product_name,
                f"{float(total_quantity):,g} {item.product.unit}",  # Use the unit from the last item processed
            ])

        # Configure table styles
        table = Table(data, colWidths=[250, 150])
        table.setStyle(TableStyle([
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ]))

        # Position the table
        table.wrapOn(pdf, width, height)
        table_width, table_height = table.wrap(0, 0)  # Get actual table height

        # Draw the table, positioning it to expand downward
        table.drawOn(pdf, 50, height - 286 - table_height)

    else:
        # Define the data for the table
        data = [["Product", "Quantity", "Unit Price", "Amount"]]

        for item in invoice.invoiceitem_set.all():
            nett_display = ""
            if item.hide_nett == False:
                nett_display = " (Nett)"
            unit_price_display = (
                item.product_type if item.product_type in ["bonus", "sample"]
                else f"${(item.net_price / item.product.units_per_pack).quantize(Decimal('0.01'), rounding=ROUND_UP):,.2f} {nett_display}" if item.net_price
                else f"${(item.price / item.product.units_per_pack).quantize(Decimal('0.01'), rounding=ROUND_UP):,.2f}"
            )

            unit_price_display += f"\n"

            product_name = item.product.name
            product_name += f"\n"
            if invoice.customer.show_registration_code and item.product.registration_code:
                product_name += f"(Reg. No.: {item.product.registration_code})"
            if invoice.customer.show_expiry_date and item.product.expiry_date:
                product_name += f" (Exp.: {item.product.expiry_date.strftime('%Y-%b-%d')})"
            data.append([
                product_name,
                f"{float(item.quantity):,g} {item.product.unit}\n",
                unit_price_display,
                f"${item.sum_price:,.2f}\n" if item.sum_price != 0 else f"-\n"
            ])

        # Create the table
        table = Table(data, colWidths=[200, 100, 100, 100])
        table.setStyle(TableStyle([
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ]))

        # Position the table
        table.wrapOn(pdf, width, height)
        table_width, table_height = table.wrap(0, 0)  # Get actual table height

        # Draw the table, positioning it to expand downward
        table.drawOn(pdf, 60, height - 286 - table_height)

        # Add total price at the bottom
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawRightString(510, height - 600, f"Total: ${invoice.total_price:,.2f}")

        encrypted_customer_id = encrypt_customer_id(invoice.customer.id)
        qr_code_image = generate_whatsapp_qr_code(str(os.getenv('PHONE_NUMBER')), encrypted_customer_id)
        qr_code_reader = ImageReader(qr_code_image)
        pdf.drawImage(qr_code_reader, 50, height - 822, width=75, height=75)
