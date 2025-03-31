import re
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal

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

from ..models import Salesman, Invoice
from ..tables import InvoiceFilter, SalesmanInvoiceTable

def sales_incentive_scheme(sales):
    if sales < 50000:
        return 0.02
    elif sales < 70000:
        return 0.025
    elif sales < 100000:
        return 0.0325
    elif sales < 130000:
        return 0.04
    elif sales < 170000:
        return 0.05
    elif sales >= 170000:
        return 0.055

@staff_member_required
def salesman_list(request):
    salesmen = Salesman.objects.all()
    return render(request, 'invoice/salesman_list.html', {'salesmen': salesmen})


@method_decorator(staff_member_required, name='dispatch')
class SalesmanInvoiceView(SingleTableMixin, FilterView):
    table_class = SalesmanInvoiceTable
    model = Invoice
    template_name = "invoice/salesman_detail.html"
    filterset_class = InvoiceFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invoices = self.get_queryset()  # Get filtered queryset

        # Get salesman from the first invoice if any exist
        context['salesman'] = invoices.first().salesman if invoices.exists() else None

        return context


def salesman_monthly_sales(request, salesman_id):
    # Get current year and start of each month in the year
    current_year = timezone.now().year
    monthly_sales = (
        Invoice.objects.filter(salesman_id=salesman_id, payment_date__year=current_year)
            .values('payment_date__month')  # Group by month
            .annotate(monthly_total=Sum('total_price'))  # Sum total_price per month
            .order_by('payment_date__month')
    )

    # Prepare data for the chart
    months = [0] * 12  # 12 months
    for sale in monthly_sales:
        month_index = sale['payment_date__month'] - 1
        months[month_index] = float(sale['monthly_total'] or 0)

    return JsonResponse({
        'months': ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        'sales': months,
    })


@staff_member_required
def salesman_monthly_preview(request, salesman_id):
    salesman = get_object_or_404(Salesman, id=salesman_id)
    latest_invoice = Invoice.objects.filter(salesman=salesman, delivery_date__isnull=False).order_by(
        '-delivery_date').first()
    breadcrumbs = [
        {"name": "Salesmen", "url": reverse("salesman_list")},
        {"name": salesman.name, "url": reverse("salesman_monthly_preview", kwargs={"salesman_id": salesman.id})},
    ]
    if latest_invoice:
        today = latest_invoice.delivery_date
    else:
        today = now().date()

    months = []

    for i in range(12):  # Get the last 12 months
        date = today.replace(day=1) - relativedelta(months=i)
        year, month = date.year, date.month

        # Calculate total amount for the salesman in the month
        total_amount = (
                Invoice.objects.filter(salesman=salesman, delivery_date__year=year, delivery_date__month=month)
                .aggregate(total=Sum("total_price"))["total"] or 0
        )

        if total_amount > 0:
            months.append({
                'year': year,
                'month': month,
                'name': date.strftime('%B %Y'),
                'total': total_amount,
                'url': reverse('salesman_monthly_report',
                               kwargs={'salesman_id': salesman.id, 'year': year, 'month': month}),
            })

    return render(request, 'invoice/salesman_monthly_preview.html',
                  {'months': months, 'salesman': salesman, "breadcrumbs": breadcrumbs})


@staff_member_required
def salesman_monthly_report(request, salesman_id, year, month):
    salesman = get_object_or_404(Salesman, id=salesman_id)
    sales_share = get_object_or_404(Salesman, name="DS/MM/AC")
    first_day = make_aware(datetime(int(year), int(month), 1))
    last_day = make_aware(datetime(int(year), int(month) + 1, 1) - timedelta(days=1))

    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.month
    show_commission_summary = True
    # Prevent showing the current month's commission report
    if int(year) == current_year and int(month) == current_month:
        show_commission_summary = False
    breadcrumbs = [
        {"name": "Salesmen", "url": reverse("salesman_list")},
        {"name": salesman.name, "url": reverse("salesman_monthly_preview", kwargs={"salesman_id": salesman.id})},
        {"name": f"{year}-{month} Report", "url": ""},
    ]
    invoices = Invoice.objects.filter(
        salesman=salesman, delivery_date__range=(first_day, last_day)
    ).prefetch_related("invoiceitem_set", "invoiceitem_set__product")
    invoice_share = Invoice.objects.filter(
        salesman=sales_share, delivery_date__range=(first_day, last_day)
    ).prefetch_related("invoiceitem_set", "invoiceitem_set__product")

    weeks = {1: {"invoices": [], "total": Decimal("0.00")},
             2: {"invoices": [], "total": Decimal("0.00")},
             3: {"invoices": [], "total": Decimal("0.00")},
             4: {"invoices": [], "total": Decimal("0.00")}}
    monthly_total = Decimal("0.00")

    for invoice in invoices:
        week_number = (invoice.delivery_date.day - 1) // 7 + 1
        if week_number in weeks:
            weeks[week_number]["invoices"].append(invoice)
            weeks[week_number]["total"] += invoice.total_price
        else:
            continue
        monthly_total += invoice.total_price

        # Group invoice items by product name without the lot number
        grouped_items = defaultdict(list)

        for item in invoice.invoiceitem_set.all():
            if item.product:
                clean_name = re.sub(r"\s*\(Lot\s*no\.?:?\s*[A-Za-z0-9-]+\)", "", item.product.name)
                grouped_items[clean_name].append(str(item.quantity))

        invoice.items = [f"{name} ({' + '.join(quantities)})" for name, quantities in grouped_items.items()]

    monthly_total_share = Decimal("0.00")
    monthly_total_share_percentage = Decimal("0.00")
    for invoice in invoice_share:
        monthly_total_share += invoice.total_price
    if salesman.name == "Dominic So":
        monthly_total_share_percentage = Decimal('0.4')
    elif salesman.name == "Alex Cheung":
        monthly_total_share_percentage = Decimal('0.3')
    elif salesman.name == "Matthew Mak":
        monthly_total_share_percentage = Decimal('0.3')
    personal_monthly_total_share = monthly_total_share * monthly_total_share_percentage
    sales_monthly_total = monthly_total + personal_monthly_total_share
    incentive_percentage = sales_incentive_scheme(sales_monthly_total)
    commission = sales_monthly_total * Decimal(str(incentive_percentage)) * Decimal("1.1")


    return render(
        request,
        "invoice/salesman_monthly_report.html",
        {"weeks": weeks, "year": year, "month": month, "monthly_total": monthly_total,
         "salesman": salesman, "commission": commission,
         "monthly_total_share": monthly_total_share,
         "monthly_total_share_percentage": monthly_total_share_percentage,
         "personal_monthly_total_share": personal_monthly_total_share,
         "sales_monthly_total": sales_monthly_total,
         "incentive_percentage": incentive_percentage,
         "show_commission_summary": show_commission_summary,
         "breadcrumbs": breadcrumbs},
    )
