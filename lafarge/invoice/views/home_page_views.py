import calendar
import logging
import re
from collections import defaultdict
from datetime import datetime

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.db.models.functions import ExtractMonth, ExtractYear
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.timezone import localdate
from django.utils.timezone import make_aware
from django.utils.timezone import now

from ..models import Invoice

logger = logging.getLogger(__name__)


@staff_member_required
def home(request):
    """Dashboard view displaying today's invoices and pending deposits."""
    start_date = make_aware(datetime(2025, 3, 19))
    today = localdate()
    invoices_today = Invoice.objects.filter(delivery_date=today).select_related(
        'customer', 'salesman'
    ).prefetch_related('invoiceitem_set__product')

    pending_deposits = Invoice.objects.filter(payment_date__isnull=False, deposit_date__isnull=True,
                                              payment_date__gte=start_date).select_related('customer')

    future_deposits = pending_deposits.filter(payment_date__gt=today)
    current_pending_deposits = pending_deposits.exclude(id__in=future_deposits.values('id'))

    total_pending_deposit = current_pending_deposits.aggregate(Sum('total_price'))['total_price__sum'] or 0

    payment_type_totals = current_pending_deposits.values('payment_method').annotate(total=Sum('total_price'))
    future_payment_type_totals = future_deposits.values('payment_method').annotate(total=Sum('total_price'))
    payment_totals_dict = {entry['payment_method']: entry['total'] for entry in payment_type_totals}
    future_payment_totals_dict = {entry['payment_method']: entry['total'] for entry in future_payment_type_totals}

    # Calculate counts for each payment method (group by cheque_detail for cheques)
    payment_counts_dict = {}
    future_payment_counts_dict = {}
    
    for payment_method in set(payment_totals_dict.keys()) | set(future_payment_totals_dict.keys()):
        # For current pending deposits
        current_invoices = current_pending_deposits.filter(payment_method=payment_method)
        if payment_method == 'cheque':
            # Count unique cheque details
            payment_counts_dict[payment_method] = len(set(current_invoices.exclude(cheque_detail__isnull=True).values_list('cheque_detail', flat=True)))
        else:
            # Count individual invoices for non-cheque payments
            payment_counts_dict[payment_method] = current_invoices.count()
        
        # For future deposits
        future_invoices = future_deposits.filter(payment_method=payment_method)
        if payment_method == 'cheque':
            # Count unique cheque details
            future_payment_counts_dict[payment_method] = len(set(future_invoices.exclude(cheque_detail__isnull=True).values_list('cheque_detail', flat=True)))
        else:
            # Count individual invoices for non-cheque payments
            future_payment_counts_dict[payment_method] = future_invoices.count()

    modified_invoices = []
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
        'invoices_today': modified_invoices,
        'pending_deposits': pending_deposits,
        'total_pending_deposit': total_pending_deposit,
        'payment_totals_dict': payment_totals_dict,
        'future_payment_totals_dict': future_payment_totals_dict,
        'payment_counts_dict': payment_counts_dict,
        'future_payment_counts_dict': future_payment_counts_dict,
    })


@staff_member_required
def sales_data(request):
    """API endpoint providing sales analytics data for charts and reports."""
    try:
        if not Invoice.objects.exists():
            return JsonResponse({"error": "No invoices found"}, status=400)

        current_date = now()
        last_month = (current_date.month - 1) or 12
        last_month_year = current_date.year if current_date.month > 1 else current_date.year - 1
        last_month_name = calendar.month_name[last_month]

        sales_per_month = (
            Invoice.objects
                .annotate(month=ExtractMonth('delivery_date'), year=ExtractYear('delivery_date'))
                .exclude(month__isnull=True)
                .exclude(month=1, year=2025)
                .values('month')
                .annotate(total_sales=Sum('total_price'))
                .order_by('month')
        )

        sales_by_salesman = (
            Invoice.objects
                .filter(delivery_date__month=last_month, delivery_date__year=last_month_year)
                .select_related('salesman')
                .values('salesman__code')
                .annotate(total_sales=Sum('total_price'))
                .exclude(salesman__code="Lafarge")
                .exclude(salesman__code="DS/MM/AC")
                .exclude(salesman__code="KK")
                .order_by('-total_sales')
        )

        data = {
            "sales_per_month": list(sales_per_month),
            "sales_by_salesman": list(sales_by_salesman),
            "last_month_name": last_month_name,
        }

        return JsonResponse(data)

    except Exception as e:
        logger.error(f"Error in sales_data: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@staff_member_required
def product_insights_data(request):
    """API endpoint providing product sales analytics for the previous month."""
    try:
        current_date = now()
        last_month = (current_date.month - 1) or 12
        last_month_year = current_date.year if current_date.month > 1 else current_date.year - 1
        last_month_name = calendar.month_name[last_month]

        product_sales = (
            Invoice.objects
                .filter(delivery_date__month=last_month, delivery_date__year=last_month_year)
                .prefetch_related('invoiceitem_set__product')
                .values('invoiceitem__product__name')
                .annotate(total_quantity=Sum('invoiceitem__quantity'))
                .order_by('-total_quantity')
        )

        data = {
            "product_sales": list(product_sales),
            "last_month_name": last_month_name,
        }
        return JsonResponse(data)

    except Exception as e:
        logger.error(f"Error in product_insights_data: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)
