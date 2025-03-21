import calendar
import logging
import re
from collections import defaultdict

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.db.models.functions import ExtractMonth, ExtractYear
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.timezone import localdate
from django.utils.timezone import now

from ..models import Invoice

logger = logging.getLogger(__name__)


@staff_member_required
def home(request):
    today = localdate()
    invoices_today = Invoice.objects.filter(delivery_date=today)

    modified_invoices = []  # Store modified invoice data

    for invoice in invoices_today:
        grouped_items = defaultdict(list)
        for item in invoice.invoiceitem_set.all():
            if item.product:
                clean_name = re.sub(r"\s*\(Lot\s*no\.?:?\s*[A-Za-z0-9-]+\)", "", item.product.name)
                grouped_items[clean_name].append(str(item.quantity))

        modified_invoices.append({
            'delivery_date': invoice.delivery_date,
            'number': invoice.number,
            'customer': invoice.customer,
            'salesman': invoice.salesman,
            'total_price': invoice.total_price,
            'items': [f"{name} ({' + '.join(quantities)})" for name, quantities in grouped_items.items()]
        })

    return render(request, 'invoice/home.html', {
        'invoices_today': modified_invoices
    })


@staff_member_required
def sales_data(request):
    try:
        # Check if invoices exist
        if not Invoice.objects.exists():
            return JsonResponse({"error": "No invoices found"}, status=400)

        # Get current date
        current_date = now()
        last_month = (current_date.month - 1) or 12
        last_month_year = current_date.year if current_date.month > 1 else current_date.year - 1
        last_month_name = calendar.month_name[last_month]  # Get month name (e.g., "February")

        # Get total sales per month
        sales_per_month = (
            Invoice.objects
                .annotate(month=ExtractMonth('delivery_date'), year=ExtractYear('delivery_date'))
                .exclude(month__isnull=True)
                .exclude(month=1, year=2025)
                .values('month')
                .annotate(total_sales=Sum('total_price'))
                .order_by('month')
        )

        # Get sales by salesman for last month
        sales_by_salesman = (
            Invoice.objects
                .filter(delivery_date__month=last_month, delivery_date__year=last_month_year)
                .values('salesman__name')
                .annotate(total_sales=Sum('total_price'))
                .order_by('-total_sales')
        )

        data = {
            "sales_per_month": list(sales_per_month),
            "sales_by_salesman": list(sales_by_salesman),
            "last_month_name": last_month_name,  # Include month name in response
        }

        return JsonResponse(data)

    except Exception as e:
        logger.error(f"Error in sales_data: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@staff_member_required
def product_insights_data(request):
    try:
        # Get current date
        current_date = now()
        last_month = (current_date.month - 1) or 12
        last_month_year = current_date.year if current_date.month > 1 else current_date.year - 1
        last_month_name = calendar.month_name[last_month]  # Get month name

        # Get total sales per product for the previous month
        product_sales = (
            Invoice.objects
                .filter(delivery_date__month=last_month, delivery_date__year=last_month_year)
                .values('invoiceitem__product__name')  # Get product name
                .annotate(total_quantity=Sum('invoiceitem__quantity'))  # Sum of quantity sold
                .order_by('-total_quantity')  # Order by highest sales
        )

        data = {
            "product_sales": list(product_sales),
            "last_month_name": last_month_name,  # Include last month's name
        }
        return JsonResponse(data)

    except Exception as e:
        logger.error(f"Error in product_insights_data: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)
