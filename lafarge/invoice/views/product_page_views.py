import re
from collections import defaultdict

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import F
from django.shortcuts import render, get_object_or_404
from django_tables2.export.export import TableExport

from ..check_utils import prefix_check
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

    transactions = InvoiceItem.objects.filter(product=product).select_related("invoice").order_by(
        F("invoice__delivery_date").desc(nulls_first=True),
        "-invoice__id",
        "-id"
    )

    customer_filter = request.GET.get('customer_filter', '').lower()
    invoice_filter = request.GET.get('invoice_filter', '').lower()
    clear_filter = request.GET.get('clear')

    transactions_data = []
    remaining_stock = product.quantity  # Start with the latest stock
    batch_match = re.search(r"\(Lot\s*no\.?:?\s*([A-Za-z0-9-]+)\)", product.name)
    if batch_match:
        batch_number = batch_match.group(1)
    else:
        batch_number = ""

    for item in transactions:
        remaining_stock += item.quantity

    initial_stock = remaining_stock

    if product.import_date and product.import_invoice_number:
        transactions_data.append({
            "invoice_number": product.import_invoice_number,
            "customer": product.supplier,
            "date": product.import_date,
            "batch_number": batch_number,
            "quantity": "-",
            "product_type": "IN",
            "remaining_stock": initial_stock,
        })
        remaining_stock = initial_stock

    transactions = transactions[::-1]

    grouped_transactions = defaultdict(lambda: {
        "customer": "",
        "sample_customer": "",
        "date": "",
        "quantity": 0,
        "remaining_stock": None
    })

    for item in transactions:
        invoice_number = item.invoice.number
        quantity_change = -item.quantity
        remaining_stock += quantity_change

        care_of = None
        if item.invoice.customer.care_of:
            if not prefix_check(item.invoice.customer.care_of.lower()):
                care_of = "Dr. " + item.invoice.customer.care_of
            else:
                care_of = item.invoice.customer.care_of
        customer_name = None
        if item.invoice.customer.name:
            if not prefix_check(item.invoice.customer.name.lower()):
                customer_name = "Dr. " + item.invoice.customer.name
            else:
                customer_name = item.invoice.customer.name
        sample_customer = None
        if item.invoice.sample_customer:
            if not prefix_check(item.invoice.sample_customer.lower()):
                sample_customer = "Dr. " + item.invoice.sample_customer
            else:
                sample_customer = item.invoice.sample_customer

        grouped_transactions[invoice_number]["customer"] = customer_name if item.invoice.customer else ""
        grouped_transactions[invoice_number]["sample_customer"] = sample_customer or ""
        grouped_transactions[invoice_number]["care_of"] = care_of if item.invoice.customer else None
        grouped_transactions[invoice_number]["date"] = item.invoice.delivery_date or "To Be Delivered"
        grouped_transactions[invoice_number]["quantity"] += quantity_change

        if grouped_transactions[invoice_number]["remaining_stock"] is None or remaining_stock < \
                grouped_transactions[invoice_number]["remaining_stock"]:
            grouped_transactions[invoice_number]["remaining_stock"] = remaining_stock

    filtered_transactions = []
    for invoice_number, data in grouped_transactions.items():

        display_name = data["care_of"] if data["care_of"] is not None else (data["sample_customer"] or data["customer"])

        transaction = {
            "invoice_number": invoice_number,
            "batch_number": batch_number,
            "customer": display_name,
            "care_of": data["care_of"],
            "date": data["date"],
            "quantity": data["quantity"],
            "product_type": "OUT",
            "remaining_stock": data["remaining_stock"],
        }

        matches_customer = True
        if customer_filter:
            customer_words = customer_filter.split()
            display_name_lower = display_name.lower() if display_name else ""
            matches_customer = any(word in display_name_lower for word in customer_words)

        matches_invoice = True
        if invoice_filter:
            invoice_str = str(invoice_number).lower()
            invoice_words = invoice_filter.split()
            matches_invoice = any(word in invoice_str for word in invoice_words)

        if matches_customer and matches_invoice:
            filtered_transactions.append(transaction)

    if product.import_date and product.import_invoice_number:
        import_transaction = {
            "invoice_number": product.import_invoice_number,
            "customer": product.supplier,
            "date": product.import_date,
            "batch_number": batch_number,
            "quantity": "-",
            "product_type": "IN",
            "remaining_stock": initial_stock,
        }

        matches_customer = True
        if customer_filter:
            customer_words = customer_filter.split()
            supplier_name = product.supplier.lower() if product.supplier else ""
            matches_customer = any(word in supplier_name for word in customer_words)

        matches_invoice = True
        if invoice_filter:
            invoice_str = str(product.import_invoice_number).lower()
            invoice_words = invoice_filter.split()
            matches_invoice = any(word in invoice_str for word in invoice_words)

        if matches_customer and matches_invoice:
            filtered_transactions.insert(0, import_transaction)

    context = {
        "product": product,
        "transactions": filtered_transactions,
    }

    return render(request, "invoice/product_transaction.html", context)
