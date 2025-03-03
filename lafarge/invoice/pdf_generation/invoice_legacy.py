from decimal import Decimal, ROUND_UP

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle
from reportlab.graphics.barcode import code128

from ..check_utils import prefix_check


def draw_invoice_page_legacy(pdf, invoice):
    """
    Draw the content of an invoice page in the PDF.

    Args:
        pdf: The ReportLab Canvas object.
        invoice: The Invoice object.
    """
    width, height = A4

    # Draw the background image
    # background_image_path = os.path.join(settings.STATIC_ROOT, 'Invoice_Legacy.png')
    # pdf.drawImage(background_image_path, 0, 0, width, height)
    pdf.setFont("Times-Bold", 12)

    # Customer information
    address_lines = [line.strip() for line in invoice.customer.address.split("\n") if line.strip()]
    delivery_address_lines = [line.strip() for line in invoice.customer.delivery_address.split("\n") if line.strip()]
    office_hour_lines = [line.strip() for line in invoice.customer.office_hour.split("\n") if line.strip()]

    y_position = height - 150 + 12
    text_object = pdf.beginText(100, y_position)
    text_object.setFont("Times-Roman", 12)
    if prefix_check(invoice.customer.name.lower()):
        text_object.textLine(f"{invoice.customer.name}")
    else:
        text_object.textLine(f"Dr. {invoice.customer.name}")
    if invoice.customer.care_of and not invoice.customer.hide_care_of:
        if prefix_check(invoice.customer.care_of.lower()):
            text_object.textLine(f"{invoice.customer.care_of}")
        else:
            text_object.textLine(f"C/O: Dr. {invoice.customer.care_of}")

    for line in address_lines:
        text_object.textLine(line)

    text_object.textLine(
        f"Tel: {invoice.customer.telephone_number or ''}"
        f"{f' ({invoice.customer.contact_person})' if invoice.customer.contact_person else ''}"
    )
    pdf.drawText(text_object)

    text_object = pdf.beginText(32, height - 440)
    text_object.setFont("Times-Roman", 10)
    if invoice.order_number:
        text_object.textLine(f"Order No.: {invoice.order_number}")
    if invoice.customer.delivery_to:
        text_object.textLine(f"Deliver To: {invoice.customer.delivery_to}")
    if invoice.customer.show_delivery_address:
        for line in delivery_address_lines:
            text_object.textLine(line)
    pdf.drawText(text_object)
    pdf.drawString(37, height - 510, f"** ALL GOODS ARE NON RETURNABLE **")

    if office_hour_lines:
        office_hour_height = 150
        if len(str(invoice.customer.name)) >= 40:
            office_hour_height = 165
        pdf.setFont("Times-Bold", 12)
        pdf.drawString(458, height - office_hour_height + 12, f"OFFICE HOURS:")
        text_object = pdf.beginText(458, height - office_hour_height - 15 + 12)
        text_object.setFont("Times-Roman", 10)
        for line in office_hour_lines:
            text_object.textLine(line)
        pdf.drawText(text_object)

    # Salesman and Date
    pdf.setFont("Times-Bold", 10)
    pdf.drawString(65, height - 100 + 5, f"{invoice.terms}")
    pdf.drawString(65, height - 120 + 5, f"{invoice.salesman.code}")

    # Table for Invoice Items
    # Define the data for the table
    data = [[" ", " ", " ", " "]]
    for item in invoice.invoiceitem_set.all():
        nett_display = ""
        if item.hide_nett == False:
            nett_display = " (Nett)"
        unit_price_display = (
            item.product_type if item.product_type in ["bonus", "sample"]
            else f"${(item.net_price / item.product.units_per_pack).quantize(Decimal('0.01'), rounding=ROUND_UP):,.2f} {nett_display}" if item.net_price
            else f"${(item.price / item.product.units_per_pack).quantize(Decimal('0.01'), rounding=ROUND_UP):,.2f}"
        )

        if invoice.customer.show_registration_code or invoice.customer.show_expiry_date:
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
        else:
            data.append([
                item.product.name,
                f"{float(item.quantity):,g} {item.product.unit}",
                unit_price_display,
                f"${item.sum_price:,.2f}" if item.sum_price != 0 else f"-"
            ])

    # Create the table
    table = Table(data, colWidths=[200, 122, 92, 100])
    table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        # ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))

    # Position the table
    table.wrapOn(pdf, width, height)
    table_width, table_height = table.wrap(0, 0)  # Get actual table height

    # Draw the table, positioning it to expand downward
    table.drawOn(pdf, 37, height - 200 - table_height)

    # Add total price at the bottom
    pdf.setFont("Times-Bold", 14)
    pdf.drawString(460, height - 430, f"${invoice.total_price:,.2f}")

    # Generate barcode from invoice number
    barcode = code128.Code128(invoice.number, barWidth=1.2, barHeight=10)

    # Position the barcode at the top of the page
    barcode_x = 250
    barcode_y = height - 20
    barcode.drawOn(pdf, barcode_x, barcode_y)