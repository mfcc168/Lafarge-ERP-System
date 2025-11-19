import re
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal

from calendar import monthrange
from dateutil.relativedelta import relativedelta
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.timezone import make_aware
from django.utils.timezone import now
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from ..decorators import user_is_lafarge_or_superuser
from ..models import Invoice, Deliveryman
from ..tables import InvoiceFilter


@user_is_lafarge_or_superuser
def deliveryman_list(request):
    deliverymen = Deliveryman.objects.all()
    return render(request, 'invoice/deliveryman_list.html', {'deliverymen': deliverymen})

@user_is_lafarge_or_superuser
def deliveryman_monthly_preview(request, deliveryman_id):
    deliveryman = get_object_or_404(Deliveryman, id=deliveryman_id)

    latest_invoice = Invoice.objects.filter(
        deliveryman=deliveryman,
        delivery_date__isnull=False
    ).order_by('-delivery_date').first()

    base_date = latest_invoice.delivery_date if latest_invoice else now().date()

    months = []
    for i in range(12):
        date = (base_date.replace(day=1) - relativedelta(months=i))
        year, month = date.year, date.month

        if year == 2025 and month == 1:
            continue

        invoice_count = Invoice.objects.filter(
            deliveryman=deliveryman,
            delivery_date__year=year,
            delivery_date__month=month
        ).count()

        if invoice_count > 0:
            months.append({
                'name': date.strftime('%B %Y'),
                'invoice_count': invoice_count,
                'url': reverse('deliveryman_monthly_report', kwargs={
                    'deliveryman_id': deliveryman.id,
                    'year': year,
                    'month': month
                }),
            })

    breadcrumbs = [
        {"name": "Deliverymen", "url": reverse("deliveryman_list")},
        {"name": deliveryman.name, "url": ""},
    ]

    return render(request, 'invoice/deliveryman_monthly_preview.html', {
        'deliveryman': deliveryman,
        'months': months,
        'breadcrumbs': breadcrumbs,
    })

@user_is_lafarge_or_superuser
def deliveryman_monthly_report(request, deliveryman_id, year, month):
    deliveryman = get_object_or_404(Deliveryman, id=deliveryman_id)

    year, month = int(year), int(month)

    first_day = make_aware(datetime(year, month, 1))
    last_day = make_aware(datetime(year, month, monthrange(year, month)[1], 23, 59, 59))

    breadcrumbs = [
        {"name": "Deliverymen", "url": reverse("deliveryman_list")},
        {"name": deliveryman.name, "url": reverse("deliveryman_monthly_preview", kwargs={"deliveryman_id": deliveryman.id})},
        {"name": f"{year}-{month:02d} Report", "url": ""},
    ]

    invoices = Invoice.objects.filter(
        deliveryman=deliveryman,
        delivery_date__range=(first_day, last_day)
    ).select_related('customer').prefetch_related('invoiceitem_set__product').order_by('delivery_date')

    daily_groups = defaultdict(list)

    for invoice in invoices:
        day = invoice.delivery_date  # already a date object
        daily_groups[day].append(invoice)

        grouped = defaultdict(list)
        for item in invoice.invoiceitem_set.all():
            if item.product:
                clean_name = re.sub(r"\s*\(Lot\s*no\.?:?\s*[A-Za-z0-9-]+\)", "", item.product.name).strip()
                grouped[clean_name].append(str(item.quantity))

        invoice.display_items = [f"{name} ({' + '.join(qtys)})" for name, qtys in grouped.items()]

    sorted_daily_groups = sorted(daily_groups.items())

    # NEW: Calculate total invoice count for the month
    total_monthly_invoices = invoices.count()  # ← This is correct and fast!

    context = {
        "deliveryman": deliveryman,
        "year": year,
        "month": month,
        "daily_groups": sorted_daily_groups,
        "breadcrumbs": breadcrumbs,
        "total_monthly_invoices": total_monthly_invoices,  # ← Add this
    }

    return render(request, "invoice/deliveryman_monthly_report.html", context)