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


@method_decorator(staff_member_required, name='dispatch')
class InvoiceListView(SingleTableMixin, FilterView):
    model = Invoice
    table_class = InvoiceTable
    template_name = "invoice/invoice_list.html"
    filterset_class = InvoiceFilter


@staff_member_required
def invoice_detail(request, invoice_number):
    # Fetch the invoice by its number
    invoice = get_object_or_404(Invoice, number=invoice_number)
    # Render the invoice template with the context
    context = {
        'invoice': invoice
    }
    return render(request, 'invoice/invoice_detail.html', context)


def monthly_preview(request):
    latest_invoice = Invoice.objects.filter(delivery_date__isnull=False).order_by('-delivery_date').first()

    if latest_invoice:
        today = latest_invoice.delivery_date
    else:
        today = now().date()  # Fallback if no invoices exist

    months = []

    for i in range(12):  # Get the last 12 months
        date = today.replace(day=1) - relativedelta(months=i)  # Correct month rollback
        year, month = date.year, date.month

        # Calculate total amount for the month
        total_amount = (
                Invoice.objects.filter(delivery_date__year=year, delivery_date__month=month)
                .aggregate(total=Sum("total_price"))["total"] or 0
        )

        # Only show months where total amount is greater than 0
        months.append({
            'year': year,
            'month': month,
            'name': date.strftime('%B %Y'),
            'total': total_amount,
            'url': reverse('monthly_report', kwargs={'year': year, 'month': month}), })

    return render(request, 'invoice/monthly_preview.html', {'months': months})


@staff_member_required
def monthly_report(request, year, month):
    first_day = make_aware(datetime(int(year), int(month), 1))
    last_day = make_aware(datetime(int(year), int(month) + 1, 1) - timedelta(days=1))

    invoices = Invoice.objects.filter(delivery_date__range=(first_day, last_day)).prefetch_related(
        "invoiceitem_set", "invoiceitem_set__product"
    )

    weeks = {
        1: {"invoices": [], "total": Decimal("0.00")},
        2: {"invoices": [], "total": Decimal("0.00")},
        3: {"invoices": [], "total": Decimal("0.00")},
        4: {"invoices": [], "total": Decimal("0.00")},
        5: {"invoices": [], "total": Decimal("0.00")},
    }
    monthly_total = Decimal("0.00")

    for invoice in invoices:
        week_number = (invoice.delivery_date.day - 1) // 7 + 1
        if week_number <= 4:
            weeks[week_number]["invoices"].append(invoice)
            weeks[week_number]["total"] += invoice.total_price
        else:
            weeks[5]["invoices"].append(invoice)  # Handle 5th week for months with >28 days
            weeks[5]["total"] += invoice.total_price  # Add to the total for the 5th week
        monthly_total += invoice.total_price

        # Group invoice items by product name without the lot number
        grouped_items = defaultdict(list)

        for item in invoice.invoiceitem_set.all():
            if item.product:
                clean_name = re.sub(r"\s*\(Lot\s*no\.?:?\s*[A-Za-z0-9-]+\)", "", item.product.name)
                grouped_items[clean_name].append(str(item.quantity))

        # Convert grouped items to a formatted list
        invoice.items = [f"{name} ({' + '.join(quantities)})" for name, quantities in grouped_items.items()]

    return render(
        request,
        "invoice/monthly_report.html",
        {"weeks": weeks, "year": year, "month": month, "monthly_total": monthly_total},
    )
