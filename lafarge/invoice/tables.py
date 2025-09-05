"""
Django Tables2 configuration for data presentation and filtering.

Defines table classes for displaying and exporting customer, invoice, and
product transaction data with custom rendering and filtering capabilities.
"""

import django_tables2 as tables
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django_filters import FilterSet, CharFilter, DateFilter, DateTimeFilter
from django_tables2.export.views import ExportMixin
from django_tables2.utils import A

from .models import Customer
from .models import Invoice
from .models import ProductTransaction
from .templatetags.custom_filter import currency


class CustomerTable(tables.Table):
    name = tables.LinkColumn(
        'customer_detail', args=[A('name'), A('care_of')],
        text=lambda record: record.name,
        attrs={'a': {'class': 'text-decoration-none'}, 'td': {'class': 'column-name'}}
    )
    care_of = tables.Column(attrs={"td": {"class": "column-care-of"}})
    address = tables.Column(attrs={"td": {"class": "column-address"}})
    office_hour = tables.Column(attrs={"td": {"class": "column-office-hour"}})
    telephone_number = tables.Column(attrs={"td": {"class": "column-telephone-number"}})

    class Meta:
        model = Customer
        attrs = {
            'class': 'table table-hover table-striped border-0 shadow-sm rounded-3',
            'th': {
                '_ordering': {
                    'orderable': 'sortable',
                    'ascending': 'ascend',
                    'descending': 'descend'
                }
            }
        }
        order_by = 'name'
        fields = ("name", "care_of", "address", "office_hour", "telephone_number")


class CustomerFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='icontains', label="Customer Name")
    care_of = CharFilter(field_name='care_of', lookup_expr='icontains', label="Care Of")
    address = CharFilter(field_name='address', lookup_expr='icontains', label="Address")
    telephone_number = CharFilter(field_name='telephone_number', lookup_expr='icontains', label="Telephone Number")

    class Meta:
        model = Customer
        fields = ["name", "care_of", "address", "telephone_number"]


class InvoiceTable(tables.Table):
    number = tables.LinkColumn(
        'invoice_detail', args=[tables.A('number')],
        text=lambda record: record.number,
    )

    customer = tables.Column(attrs={"td": {"class": "column-customer"}})

    def render_number(self, value):
        """Render invoice number with styling."""
        return mark_safe(f'<span class="text-decoration-none fw-bold text-primary">#{escape(value)}</span>')

    def render_salesman(self, value):
        """Render salesman code as styled badge."""
        return mark_safe(f'<span class="badge bg-secondary text-white">{escape(value.code)}</span>')

    def render_total_price(self, value):
        """Render total price with currency formatting."""
        return mark_safe(f'<span class="text-end fw-bold text-success">${escape(currency(value))}</span>')

    class Meta:
        model = Invoice
        attrs = {
            'class': 'table table-hover table-striped align-middle border-0 rounded-3 invoice-table',
            'th': {
                '_ordering': {
                    'orderable': 'sortable',
                    'ascending': 'ascend',
                    'descending': 'descend'
                }
            }
        }
        order_by = '-id'
        fields = ("id", "number", "customer", "delivery_date", "payment_date", "deposit_date", "salesman", "total_price")

    id = tables.Column(visible=False)


class InvoiceFilter(FilterSet):
    customer_name = CharFilter(field_name='customer__name', lookup_expr='icontains', label="Customer Name")
    customer_care_of = CharFilter(field_name='customer__care_of', lookup_expr='icontains', label="Care Of")
    delivery_date = DateFilter(field_name='delivery_date', lookup_expr='gte', label="Delivery Date (From)")
    delivery_date_to = DateFilter(field_name='delivery_date', lookup_expr='lte', label="Delivery Date (To)")
    payment_date = DateFilter(field_name='payment_date', lookup_expr='gte', label="Payment Date (From)")
    payment_date_to = DateFilter(field_name='payment_date', lookup_expr='lte', label="Payment Date (To)")
    deposit_date = DateFilter(field_name='deposit_date', lookup_expr='gte', label="Deposit Date (From)")
    deposit_date_to = DateFilter(field_name='deposit_date', lookup_expr='lte', label="Deposit Date (To)")


    class Meta:
        model = Invoice
        fields = ["number", "salesman"]  # Only include direct model fields here


from django.urls import reverse
class CustomerInvoiceTable(ExportMixin, tables.Table):
    number = tables.LinkColumn(
        'invoice_detail',
        args=[A('number')],
        text=lambda record: record.number,
        attrs={'a': {'class': 'text-decoration-none fw-bold text-primary'}}
    )

    total_price = tables.Column(
        verbose_name='Total Price',
        attrs={'td': {'class': 'text-end text-danger fw-bold'}}
    )

    delivery_date = tables.DateColumn(
        verbose_name='Delivery Date',
        attrs={'td': {'class': 'text-center'}}
    )

    payment_date = tables.DateColumn(
        verbose_name='Payment Date',
        attrs={'td': {'class': 'text-center'}}
    )

    items = tables.TemplateColumn(
        template_code='''
            <ul class="list-unstyled mb-0">
                {% for item in record.invoiceitem_set.all %}
                    <li class="small text-muted">
                        <span class="fw-bold">{{ item.product.name }}</span>: 
                        {{ item.quantity }}  @ 
                        {% if item.product_type == "normal" %}
                            <span class="text-primary">${{ item.price }}</span>
                        {% else %}
                            ({{ item.product_type }})
                        {% endif %}
                    </li>
                {% endfor %}
            </ul>
        ''',
        verbose_name="Items",
        attrs={'td': {'class': 'small'}}
    )

    # Column for copying existing orders
    copy_order = tables.TemplateColumn(
        template_name='invoice/copy_order_button.html',
        verbose_name='Copy Order',
        orderable=False,
        attrs={
            'td': {
                'class': 'text-center'
            },
            'th': {
                'class': 'text-center bg-light text-dark text-uppercase'
            }
        }
    )

    def render_total_price(self, value):
        """Render price with currency formatting and styling."""
        return mark_safe(f"<span class='text-danger fw-bold'>${currency(value)}</span>")

    class Meta:
        model = Invoice
        fields = ("number", "total_price", "delivery_date", "payment_date", "items", "copy_order")
        attrs = {
            'class': 'table table-hover table-striped shadow-sm rounded-3 bg-white border',
            'th': {
                '_ordering': {
                    'orderable': 'sortable',
                    'ascending': 'ascend',
                    'descending': 'descend'
                },
                'class': 'bg-light text-dark text-uppercase'
            }
        }


class ProductTransactionTable(tables.Table):
    timestamp = tables.DateTimeColumn(format='Y-m-d')
    invoice_number = tables.Column(accessor='description', verbose_name='Invoice Number')
    customer = tables.Column(empty_values=(), verbose_name='Customer')
    nature_of_transaction = tables.Column(empty_values=(), verbose_name='Nature of Transaction')

    def render_invoice_number(self, record):
        """Extract invoice number from transaction description."""
        if 'invoice #' in record.description:
            parts = record.description.split('invoice #')
            if len(parts) > 1:
                return parts[1].split(' ')[0].strip()
        return "N/A"

    def render_customer(self, record):
        """Extract customer name from transaction description."""
        if 'from ' in record.description:
            parts = record.description.split('from ')
            if len(parts) > 1:
                return parts[1].strip()
        return "N/A"

    def render_nature_of_transaction(self, record):
        return "IN" if record.change > 0 else "OUT"

    def render_change(self, value):
        """Format quantity change with appropriate sign."""
        return f"+{value}" if value > 0 else str(value)

    class Meta:
        model = ProductTransaction
        fields = (
            "invoice_number", "customer", "nature_of_transaction", "change", "quantity_after_transaction", "timestamp")
        attrs = {
            'class': 'table table-striped table-bordered',
        }


class ProductTransactionFilter(FilterSet):
    timestamp_from = DateTimeFilter(field_name='timestamp', lookup_expr='gte', label="Timestamp From")
    timestamp_to = DateTimeFilter(field_name='timestamp', lookup_expr='lte', label="Timestamp To")

    class Meta:
        model = ProductTransaction
        fields = []


class SalesmanInvoiceTable(ExportMixin, tables.Table):
    number = tables.LinkColumn(
        'invoice_detail', args=[A('number')],
        text=lambda record: record.number,
        attrs={'a': {'class': 'text-decoration-none fw-bold text-primary'}}
    )

    customer = tables.Column(
        accessor='customer.name',
        verbose_name='Customer Name',
        attrs={'td': {'class': 'fw-bold'}}
    )

    payment_date = tables.DateColumn(
        verbose_name="Payment Date",
        attrs={'td': {'class': 'text-center'}}
    )

    delivery_date = tables.DateColumn(
        verbose_name="Delivery Date",
        attrs={'td': {'class': 'text-center'}}
    )

    total_amount = tables.Column(
        empty_values=(),
        verbose_name="Total Amount",
        attrs={'td': {'class': 'text-end text-danger fw-bold'}}
    )

    items = tables.TemplateColumn(
        template_code='''
        <ul class="list-unstyled mb-0">
            {% for item in record.invoiceitem_set.all %}
                <li class="small text-muted">
                    <strong>{{ item.product.name }}</strong>: 
                    {{ item.quantity }} {{ item.product.unit }} @ 
                    {% if item.product_type == "normal" %}
                        <span class="text-primary">${{ item.price }}</span>
                    {% else %}
                        ({{ item.product_type }})
                    {% endif %}
                </li>
            {% endfor %}
        </ul>
        ''',
        verbose_name="Items",
        attrs={'td': {'class': 'small'}}
    )

    def render_total_amount(self, record):
        """Calculate and render total amount for invoice items."""
        return mark_safe(
            f"<span class='text-danger fw-bold'>${sum(item.sum_price for item in record.invoiceitem_set.all()):,.2f}</span>")

    class Meta:
        model = Invoice
        fields = ("number", "customer", "items", "payment_date", "delivery_date", "total_amount")
        attrs = {
            'class': 'table table-hover table-striped shadow-sm rounded-3 bg-white border',
            'th': {
                '_ordering': {
                    'orderable': 'sortable',
                    'ascending': 'ascend',
                    'descending': 'descend'
                },
                'class': 'bg-light text-dark text-uppercase'
            }
        }
