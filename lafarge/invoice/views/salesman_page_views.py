from django.utils import timezone

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django_tables2.export.export import TableExport

from ..models import Salesman, Invoice
from ..tables import InvoiceFilter, SalesmanInvoiceTable


@staff_member_required
def salesman_list(request):
    salesmen = Salesman.objects.all()
    return render(request, 'invoice/salesman_list.html', {'salesmen': salesmen})


@staff_member_required
def salesman_detail(request, salesman_id):
    salesman = get_object_or_404(Salesman, id=salesman_id)
    invoices = Invoice.objects.filter(salesman=salesman)

    # Initialize filter with request data
    filter = InvoiceFilter(request.GET, queryset=invoices)
    filter.form.fields.pop('salesman', None)
    table = SalesmanInvoiceTable(filter.qs)  # Use filtered queryset

    # Handle export
    export_format = request.GET.get("_export", None)
    if export_format:
        exporter = TableExport(export_format, table)
        return exporter.response(f"{salesman.name}_invoices.{export_format}")

    return render(request, 'invoice/salesman_detail.html', {
        'salesman': salesman,
        'table': table,
        'filter': filter,
    })


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
