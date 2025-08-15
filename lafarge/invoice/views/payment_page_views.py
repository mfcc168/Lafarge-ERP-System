import re
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.timezone import make_aware
from django.utils.timezone import now
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin

from ..models import Invoice
from ..tables import InvoiceTable, InvoiceFilter

def monthly_payment_preview(request):
    latest_invoice = Invoice.objects.filter(payment_date__isnull=False).order_by('-payment_date').first()

    if latest_invoice:
        today = latest_invoice.payment_date
    else:
        today = now().date()  # Fallback if no invoices exist

    months = []

    for i in range(12):  # Get the last 12 months
        date = today.replace(day=1) - relativedelta(months=i)  # Correct month rollback
        year, month = date.year, date.month
        # Exclude January 2025
        if year == 2025 and month == 1:
            continue
        total_amount = (
                Invoice.objects.filter(payment_date__year=year, payment_date__month=month)
                .aggregate(total=Sum("total_price"))["total"] or 0
        )

        # Only show months where total amount is greater than 0
        months.append({
            'year': year,
            'month': month,
            'name': date.strftime('%B %Y'),
            'total': total_amount,
            'url': reverse('monthly_report', kwargs={'year': year, 'month': month}), })

    return render(request, 'invoice/monthly_payment_preview.html', {'months': months})


@staff_member_required
def monthly_payment_report(request, year, month):
    first_day = make_aware(datetime(int(year), int(month), 1))
    last_day = make_aware(datetime(int(year), int(month) + 1, 1) - timedelta(days=1))

    invoices = Invoice.objects.filter(payment_date__range=(first_day, last_day)).prefetch_related(
        "invoiceitem_set", "invoiceitem_set__product"
    ).order_by('cheque_detail', 'payment_date')
    grouped_invoices = {}
    for invoice in invoices:
        cheque_detail = invoice.cheque_detail
        if cheque_detail not in grouped_invoices:
            grouped_invoices[cheque_detail] = {
                'invoices': [],
                'total_price': 0
            }
        grouped_invoices[cheque_detail]['invoices'].append(invoice)
        grouped_invoices[cheque_detail]['total_price'] += invoice.total_price
    return render(
        request,
        "invoice/monthly_payment_report.html",
        {"year": year, "month": month, "grouped_invoices": grouped_invoices},
    )