import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from django.conf import settings


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
    else:
        background_image_path = os.path.join(settings.STATIC_ROOT, 'Invoice.png')
    pdf.drawImage(background_image_path, 0, 0, width, height)

    # Set title font and position based on the copy type
    if copy_type == "Customer Copy" or copy_type == "Company Copy":
        pdf.setFont("Helvetica-Bold", 20)
        pdf.drawString(385, height - 50, copy_type)

    elif copy_type == "Original":
        pdf.setFont("Helvetica-Bold", 20)
        pdf.drawString(460, height - 50, copy_type)

    # Customer information
    address_lines = [line.strip() for line in invoice.customer.address.split("\n") if line.strip()]
    office_hour_lines = [line.strip() for line in invoice.customer.office_hour.split("\n") if line.strip()]
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(70, height - 215, f"Sold To: {invoice.customer.name}")
    pdf.drawString(70, height - 235, f"Care Of: {invoice.customer.care_of}" if invoice.customer.care_of else "")
    y_position = height - 255
    # Create a TextObject for multi-line address
    text_object = pdf.beginText(70, y_position)
    text_object.setFont("Helvetica", 10)
    for line in address_lines:
        text_object.textLine(line)

    text_object.textLine(f"Tel: {invoice.customer.telephone_number} ({invoice.customer.contact_person})" if invoice.customer.telephone_number else "")
    pdf.drawText(text_object)

    text_object = pdf.beginText(450, y_position)
    text_object.setFont("Helvetica", 10)
    for line in office_hour_lines:
        text_object.textLine(line)
    pdf.drawText(text_object)



    #pdf.drawString(350, height - 215, f"Office Hour: {invoice.customer.available_from} to {invoice.customer.available_to}")
    #pdf.drawString(350, height - 235, f"Close on: {invoice.customer.close_day}" if invoice.customer.close_day else "")

    # Salesman and Date
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(70, height - 110, f"Date : ")
    pdf.drawString(70, height - 130, f"Invoice No. : {invoice.number}")
    pdf.drawString(70, height - 150, f"Salesman : {invoice.salesman.name}")
    if copy_type != "Poison Form":
        pdf.drawString(70, height - 170, f"Terms : ")

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
        data = [["Quantity", "Product"]]
        for product_name, total_quantity in product_quantities.items():
            data.append([
                f"{total_quantity} {item.product.unit}",  # Use the unit from the last item processed
                product_name,
            ])

        # Configure table styles
        table = Table(data, colWidths=[50, 250])
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
        table.drawOn(pdf, 175, height - 450)

    else:
        data = [["Quantity", "Product", "Unit Price", "Amount"]]
        for item in invoice.invoiceitem_set.all():
            # Check if the item type is "bonus" or "sample"
            unit_price_display = item.product_type if item.product_type in ["bonus",
                                                                            "sample"] else f"${item.net_price:,.2f} (Net Price)" if item.net_price else f"${item.price:,.2f}"

            data.append([
                f"{item.quantity} {item.product.unit}",
                item.product.name,  # Display product name in the Product column
                unit_price_display,  # Display the type or the price in the Unit Price column
                f"${item.sum_price:,.2f}" if item.sum_price != 0 else "-"
            ])

        # Configure table styles
        table = Table(data, colWidths=[50, 250, 100, 100])
        table.setStyle(TableStyle([
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),  # Header text color
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Center alignment for all cells
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Header font
            ('FONTSIZE', (0, 0), (-1, 0), 12),  # Larger font size for header
            ('FONTSIZE', (0, 1), (-1, -1), 10),  # Smaller font size for the rest of the table
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # Padding for the header
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),  # Background color for the rest of the table

        ]))

        # Position the table
        table.wrapOn(pdf, width, height)
        table.drawOn(pdf, 50, height - 450)

        # Add total price at the bottom
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(400, height - 620, f"Total: ${invoice.total_price:,.2f}")
