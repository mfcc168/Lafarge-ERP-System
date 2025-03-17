from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404
from django_tables2.export.export import TableExport

from ..models import Product, ProductTransaction
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
