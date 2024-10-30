import django_tables2 as tables
from django_filters import FilterSet, CharFilter, DateFilter
from django_tables2.utils import A

from .models import Customer
from .models import Invoice


class CustomerTable(tables.Table):
    name = tables.LinkColumn('customer_detail', args=[A('name')], text=lambda record: record.name,
                             attrs={'a': {'class': 'text-decoration-none'}})

    class Meta:
        model = Customer
        attrs = {
            'class': 'table table-striped table-bordered',
            'th': {
                '_ordering': {
                    'orderable': 'sortable',  # Instead of `orderable`
                    'ascending': 'ascend',  # Instead of `asc`
                    'descending': 'descend'  # Instead of `desc`
                }
            }
        }
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
    number = tables.LinkColumn('invoice_detail', args=[A('number')], text=lambda record: record.number,
                               attrs={'a': {'class': 'text-decoration-none'}})

    class Meta:
        model = Invoice
        attrs = {
            'class': 'table table-striped table-bordered',
            'th': {
                '_ordering': {
                    'orderable': 'sortable',  # Instead of `orderable`
                    'ascending': 'ascend',  # Instead of `asc`
                    'descending': 'descend'  # Instead of `desc`
                }
            }
        }
        order_by = '-id'
        fields = ("id", "number", "customer", "delivery_date", "payment_date", "salesman", "total_price")


class InvoiceFilter(FilterSet):
    customer_name = CharFilter(field_name='customer__name', lookup_expr='icontains', label="Customer Name")
    delivery_date = DateFilter(field_name='delivery_date', lookup_expr='gte', label="Delivery Date (From)")
    delivery_date_to = DateFilter(field_name='delivery_date', lookup_expr='lte', label="Delivery Date (To)")
    payment_date = DateFilter(field_name='payment_date', lookup_expr='gte', label="Payment Date (From)")
    payment_date_to = DateFilter(field_name='payment_date', lookup_expr='lte', label="Payment Date (To)")

    class Meta:
        model = Invoice
        fields = ["number", "salesman"]  # Only include direct model fields here
