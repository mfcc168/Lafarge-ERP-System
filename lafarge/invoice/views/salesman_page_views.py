from django.utils import timezone

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django_tables2.export.export import TableExport
from django_tables2.views import SingleTableMixin
from django_filters.views import FilterView

from ..models import Salesman, Invoice
from ..tables import InvoiceFilter, SalesmanInvoiceTable


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
