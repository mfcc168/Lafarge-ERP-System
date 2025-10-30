import re
from collections import defaultdict
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.timezone import make_aware, now

from ..models import Invoice, InvoiceItem
from ..decorators import user_is_lafarge_or_superuser


@user_is_lafarge_or_superuser
def monthly_analyze_preview(request):
    """Display monthly analysis cards similar to invoice monthly preview."""
    latest_invoice = Invoice.objects.filter(delivery_date__isnull=False).order_by('-delivery_date').first()

    if latest_invoice:
        today = latest_invoice.delivery_date
    else:
        today = now().date()

    months = []

    for i in range(12):  # Get the last 12 months
        date = today.replace(day=1) - relativedelta(months=i)
        year, month = date.year, date.month
        # Skip January 2025 per business requirement
        if year == 2025 and month == 1:
            continue

        # Calculate total products sold (by revenue)
        total_revenue = (
            InvoiceItem.objects
            .filter(invoice__delivery_date__year=year, invoice__delivery_date__month=month)
            .aggregate(total=Sum("sum_price"))["total"] or 0
        )

        # Count unique products (cleaned names)
        invoice_items = (
            InvoiceItem.objects
            .filter(invoice__delivery_date__year=year, invoice__delivery_date__month=month)
            .select_related('product')
            .values('product__name')
        )

        unique_products = set()
        for item in invoice_items:
            if item['product__name']:
                clean_name = re.sub(r"\s*\(Lot\s*no\.?:?\s*[A-Za-z0-9-]+\)", "", item['product__name'])
                unique_products.add(clean_name)

        # Include all months regardless of sales volume
        months.append({
            'year': year,
            'month': month,
            'name': date.strftime('%B %Y'),
            'total_revenue': total_revenue,
            'product_count': len(unique_products),
            'url': reverse('monthly_analyze_detail', kwargs={'year': year, 'month': month}),
        })

    return render(request, 'invoice/monthly_analyze_preview.html', {'months': months})


@user_is_lafarge_or_superuser
def monthly_analyze_detail(request, year, month):
    """Display detailed monthly product analysis with horizontal bar chart."""
    # Get all invoice items for the specified month
    invoice_items = (
        InvoiceItem.objects
        .filter(invoice__delivery_date__year=year, invoice__delivery_date__month=month)
        .select_related('product')
        .values('product__name', 'sum_price', 'quantity')
    )

    # Group by cleaned product name (without lot numbers)
    grouped_products = defaultdict(lambda: {'revenue': 0.0, 'quantity': 0.0})
    for item in invoice_items:
        if item['product__name']:
            clean_name = re.sub(r"\s*\(Lot\s*no\.?:?\s*[A-Za-z0-9-]+\)", "", item['product__name'])
            grouped_products[clean_name]['revenue'] += float(item['sum_price'] or 0)
            grouped_products[clean_name]['quantity'] += float(item['quantity'] or 0)

    # Convert to list format and sort by revenue
    product_analysis = [
        {
            'name': name,
            'revenue': data['revenue'],
            'quantity': data['quantity']
        }
        for name, data in sorted(grouped_products.items(), key=lambda x: x[1]['revenue'], reverse=True)
    ]

    # Calculate month name
    month_name = datetime(year, month, 1).strftime('%B %Y')

    context = {
        'year': year,
        'month': month,
        'month_name': month_name,
        'product_analysis': product_analysis,
        'total_revenue': sum(p['revenue'] for p in product_analysis),
        'total_products': len(product_analysis),
    }

    return render(request, 'invoice/monthly_analyze_detail.html', context)


@staff_member_required
def monthly_analyze_api(request, year, month):
    """API endpoint for monthly product analysis data."""
    try:
        # Get all invoice items for the specified month
        invoice_items = (
            InvoiceItem.objects
            .filter(invoice__delivery_date__year=year, invoice__delivery_date__month=month)
            .select_related('product')
            .values('product__name', 'sum_price', 'quantity')
        )

        # Group by cleaned product name (without lot numbers)
        grouped_products = defaultdict(lambda: {'revenue': 0.0, 'quantity': 0.0})
        for item in invoice_items:
            if item['product__name']:
                clean_name = re.sub(r"\s*\(Lot\s*no\.?:?\s*[A-Za-z0-9-]+\)", "", item['product__name'])
                grouped_products[clean_name]['revenue'] += float(item['sum_price'] or 0)
                grouped_products[clean_name]['quantity'] += float(item['quantity'] or 0)

        # Convert to list format and sort by revenue
        product_data = [
            {
                'name': name,
                'revenue': data['revenue'],
                'quantity': data['quantity']
            }
            for name, data in sorted(grouped_products.items(), key=lambda x: x[1]['revenue'], reverse=True)
        ]

        data = {
            'products': product_data,
            'month_name': datetime(year, month, 1).strftime('%B %Y'),
            'total_revenue': sum(p['revenue'] for p in product_data),
            'total_products': len(product_data),
        }

        return JsonResponse(data)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)