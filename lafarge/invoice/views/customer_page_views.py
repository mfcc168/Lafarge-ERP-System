from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from django_tables2.config import RequestConfig
from django_tables2.export.export import TableExport

from ..models import Customer, Invoice
from ..tables import CustomerTable, InvoiceFilter, CustomerFilter, CustomerInvoiceTable


@method_decorator(staff_member_required, name='dispatch')
class CustomerListView(SingleTableMixin, FilterView):
    model = Customer
    table_class = CustomerTable
    template_name = "invoice/customer_list.html"
    filterset_class = CustomerFilter


@staff_member_required
def customer_detail(request, customer_name):
    customer = get_object_or_404(Customer, name=customer_name)
    invoices = Invoice.objects.filter(customer=customer)

    # Apply filter to the invoices queryset
    filterset = InvoiceFilter(request.GET, queryset=invoices)
    table = CustomerInvoiceTable(filterset.qs)
    RequestConfig(request).configure(table)

    # Check for export format in request and handle CSV export
    export_format = request.GET.get("_export", None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)  # Pass the table instance here
        return exporter.response(f"{customer_name}_invoices.{export_format}")

    context = {
        'customer': customer,
        'table': table,
        'filter': filterset,
    }
    return render(request, 'invoice/customer_detail.html', context)


@staff_member_required
def customers_with_unpaid_invoices(request):
    # Fetch customers who have at least one unpaid invoice with delivery_date not null
    customers = Customer.objects.filter(
        invoice__payment_date__isnull=True,
        invoice__delivery_date__isnull=False
    ).distinct().exclude(name="Sample")

    # Fetch unpaid invoices with delivery_date not null
    unpaid_invoices = Invoice.objects.filter(
        payment_date__isnull=True,
        delivery_date__isnull=False
    ).exclude(number__startswith="S-")

    # Filter customer data to include only those with at least one unpaid invoice
    customer_data = []
    for customer in customers:
        customer_unpaid_invoices = unpaid_invoices.filter(customer=customer)
        if customer_unpaid_invoices.exists():  # Ensure at least one unpaid invoice
            # Calculate the total unpaid amount for this customer
            customer_total_unpaid = customer_unpaid_invoices.aggregate(
                total=Sum('total_price')
            )['total'] or 0  # Default to 0 if no unpaid invoices

            customer_data.append({
                "customer": customer,
                "unpaid_invoices": customer_unpaid_invoices,
                "total_unpaid": customer_total_unpaid,
            })

    # Calculate the total unpaid amount for all invoices with delivery_date not null
    total_unpaid = unpaid_invoices.aggregate(total=Sum('total_price'))['total'] or 0

    # Calculate monthly unpaid totals for invoices with delivery_date not null
    monthly_unpaid = (
        unpaid_invoices
            .annotate(month=TruncMonth('delivery_date'))
            .values('month')
            .annotate(total=Sum('total_price'))
            .order_by('month')
    )

    context = {
        'customers': customers,
        'total_unpaid': total_unpaid,
        'monthly_unpaid': monthly_unpaid,
        'customer_data': customer_data,
    }
    return render(request, 'invoice/customers_with_unpaid_invoices.html', context)


@staff_member_required
def unpaid_invoices_by_customer(request, customer_name):
    customer = get_object_or_404(Customer, name=customer_name)
    unpaid_invoices = Invoice.get_unpaid_invoices().filter(customer=customer)

    return render(request, "invoice/unpaid_invoices_by_customer.html", {
        "customer": customer,
        "unpaid_invoices": unpaid_invoices,
    })
