from datetime import datetime, timezone
import re

from django.db.models import Q
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from django_tables2.config import RequestConfig
from django_tables2.export.export import TableExport

from ..models import Customer, Invoice, InvoiceItem
from ..number_generation_utils import generate_next_number
from ..tables import CustomerTable, InvoiceFilter, CustomerFilter, CustomerInvoiceTable


@method_decorator(staff_member_required, name='dispatch')
class CustomerListView(SingleTableMixin, FilterView):
    model = Customer
    table_class = CustomerTable
    template_name = "invoice/customer_list.html"
    filterset_class = CustomerFilter


@staff_member_required
def customer_detail(request, customer_name, customer_care_of):
    """Display customer details with filterable invoice history and export functionality."""
    customer = get_object_or_404(Customer, Q(name=customer_name) & (Q(care_of=customer_care_of) | Q(care_of__isnull=True)))
    invoices = Invoice.objects.filter(customer=customer)

    # Filter invoice history based on request parameters
    filter = InvoiceFilter(request.GET, queryset=invoices)
    filter.form.fields.pop('number', None)
    filter.form.fields.pop('salesman', None)
    filter.form.fields.pop('customer_care_of', None)
    filter.form.fields.pop('customer_name', None)
    table = CustomerInvoiceTable(filter.qs)
    RequestConfig(request).configure(table)

    # Handle data export if requested
    export_format = request.GET.get("_export", None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)  # Pass the table instance here
        return exporter.response(f"{customer_name}_invoices.{export_format}")

    context = {
        'customer': customer,
        'table': table,
        'filter': filter,
    }
    return render(request, 'invoice/customer_detail.html', context)


@staff_member_required
def customers_with_unpaid_invoices(request):
    # Fetch customers who have at least one unpaid invoice with delivery_date not null
    customers = Customer.objects.filter(
        invoice__payment_date__isnull=True,
        invoice__delivery_date__isnull=False
    ).distinct().exclude(name="Sample").select_related('salesman')

    # Fetch unpaid invoices with delivery_date not null
    unpaid_invoices = Invoice.objects.filter(
        payment_date__isnull=True,
        delivery_date__isnull=False
    ).exclude(number__startswith="S-").select_related('customer', 'salesman')

    # Filter customer data to include only those with at least one unpaid invoice
    customer_data = []
    for customer in customers:
        customer_unpaid_invoices = unpaid_invoices.filter(customer=customer)
        if customer_unpaid_invoices.exists():  # Ensure at least one unpaid invoice
            customer_total_unpaid = customer_unpaid_invoices.aggregate(
                total=Sum('total_price')
            )['total'] or 0  # Default to 0 if no unpaid invoices

            customer_data.append({
                "customer": customer,
                "unpaid_invoices": customer_unpaid_invoices,
                "total_unpaid": customer_total_unpaid,
            })

    total_unpaid = unpaid_invoices.aggregate(total=Sum('total_price'))['total'] or 0

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
def unpaid_invoices_by_customer(request, customer_name, customer_care_of):
    if customer_care_of == '':
        customer_care_of = None
    customer = get_object_or_404(Customer, Q(name=customer_name) & (Q(care_of=customer_care_of) | Q(care_of__isnull=True)))
    unpaid_invoices = Invoice.get_unpaid_invoices().filter(customer=customer)

    return render(request, "invoice/unpaid_invoices_by_customer.html", {
        "customer": customer,
        "unpaid_invoices": unpaid_invoices,
    })


@staff_member_required
def unpaid_invoices_by_month_detail(request, year_month):
    # Convert 'YYYY-MM' string to a datetime object
    try:
        selected_month = datetime.strptime(year_month, "%Y-%m")
    except ValueError:
        return render(request, 'invoice/error.html', {"message": "Invalid month format"})

    # Fetch invoices for the given month
    unpaid_invoices = Invoice.objects.filter(
        payment_date__isnull=True,
        delivery_date__year=selected_month.year,
        delivery_date__month=selected_month.month
    ).exclude(number__startswith="S-")

    total_unpaid = unpaid_invoices.aggregate(Sum('total_price'))['total_price__sum'] or 0

    context = {
        'year_month': selected_month.strftime("%B %Y"),
        'unpaid_invoices': unpaid_invoices,
        'total_unpaid': total_unpaid,
    }
    return render(request, 'invoice/unpaid_invoices_by_month_detail.html', context)


@staff_member_required
def copy_previous_order(request, invoice_number):
    original_invoice = get_object_or_404(
        Invoice.objects.select_related('customer', 'salesman').prefetch_related('invoiceitem_set__product'),
        number=invoice_number
    )


    new_number = generate_next_number()

    new_invoice = Invoice.objects.create(
        number=new_number,
        customer=original_invoice.customer,
        salesman=original_invoice.salesman,
        deliveryman=original_invoice.deliveryman,
        terms=original_invoice.terms,
        # Leave other dates blank
    )

    # Copy all invoice items
    for item in original_invoice.invoiceitem_set.all():
        available_stock = item.product.quantity

        if item.quantity <= 0:
            continue  # Skip zero or negative quantity

        if item.quantity > available_stock:
            continue  # Skip if not enough stock
            
        InvoiceItem.objects.create(
            invoice=new_invoice,
            product=item.product,
            quantity=item.quantity,
            price=item.price,
            net_price=item.net_price,
            hide_nett=item.hide_nett,
            product_type=item.product_type
        )

    return HttpResponseRedirect(reverse('admin:invoice_invoice_change', args=[new_invoice.id]))
