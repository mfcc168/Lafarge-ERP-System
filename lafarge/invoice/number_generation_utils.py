import re
from .models import Invoice


def extract_number(invoice_str):
    digits = re.findall(r'\d+', invoice_str)
    return int(''.join(digits)) if digits else 0


def generate_next_number():
    invoices = Invoice.objects.all()
    # Extract all numbers from existing invoices
    existing_numbers = [extract_number(invoice.number) for invoice in invoices if invoice.number]
    max_num = max(existing_numbers) if existing_numbers else 0

    new_num = max_num + 1

    # Ensure the number doesn't already exist
    while Invoice.objects.filter(number=f"{new_num}").exists():
        new_num += 1

    return f"{new_num}"
