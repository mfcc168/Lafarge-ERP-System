from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
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
