"""
Utility functions for generating sequential invoice numbers.

Provides functionality to extract numeric values from invoice strings
and generate unique sequential invoice numbers.
"""

import re
from .models import Invoice


def extract_number(invoice_str):
    """Extract numeric portion from invoice number string."""
    digits = re.findall(r'\d+', invoice_str)
    return int(''.join(digits)) if digits else 0


def generate_next_number():
    """
    Generate the next sequential invoice number.
    
    Finds the highest existing numeric invoice number and returns the next
    available sequential number, ensuring no duplicates exist.
    
    Returns:
        str: Next available invoice number
    """
    # Query all invoices with valid numbers
    from django.db.models import Max
    invoices = Invoice.objects.exclude(number__isnull=True).exclude(number='')
    
    # Convert invoice numbers to integers for comparison
    existing_numbers = [extract_number(invoice.number) for invoice in invoices]
    max_num = max(existing_numbers) if existing_numbers else 0

    new_num = max_num + 1

    # Handle edge case where generated number already exists
    while Invoice.objects.filter(number=str(new_num)).exists():
        new_num += 1

    return str(new_num)
