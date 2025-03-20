from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404
from django_tables2.export.export import TableExport

from ..models import Product, ProductTransaction, InvoiceItem
from ..tables import ProductTransactionTable, ProductTransactionFilter


@staff_member_required
def product_list(request):
    products = Product.objects.all().order_by('name')
    return render(request, 'invoice/product_list.html', {'products': products})


@staff_member_required
def product_transaction_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    transactions = ProductTransaction.objects.filter(product=product).order_by('timestamp')

    # Apply filter
    filterset = ProductTransactionFilter(request.GET, queryset=transactions)
    table = ProductTransactionTable(filterset.qs)

    # Handle export
    export_format = request.GET.get("_export", None)
    if export_format:
        exporter = TableExport(export_format, table)
        return exporter.response(f"{product.name}_transactions.{export_format}")

    return render(request, 'invoice/product_transaction_detail.html', {
        'product': product,
        'transactions': filterset.qs,
        'table': table,
        'filter': filterset
    })


def product_transaction_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Fetch transactions sorted by date (oldest first)
    transactions = InvoiceItem.objects.filter(product=product).select_related("invoice").order_by(
        "invoice__delivery_date", "id")

    transactions_data = []

    # Calculate the initial stock before the first transaction
    initial_stock = product.quantity + sum(item.quantity for item in transactions)

    remaining_stock = initial_stock  # Start from calculated initial stock

    for item in transactions:
        quantity_change = -item.quantity  # All transactions reduce stock

        remaining_stock += quantity_change  # Deduct from remaining stock

        transactions_data.append({
            "invoice_number": item.invoice.number,
            "customer": item.invoice.customer.name,
            "date": item.invoice.delivery_date,
            "quantity": quantity_change,
            "product_type": "OUT",
            "remaining_stock": remaining_stock,
        })

    context = {
        "product": product,
        "transactions": transactions_data,
    }

    return render(request, "invoice/product_transaction.html", context)