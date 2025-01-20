from django.contrib import admin
from django.db.models import Q
from .models import Customer, Salesman, Deliveryman, Invoice, InvoiceItem, Product, ProductTransaction

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'care_of', 'address', 'telephone_number')
    search_fields = ('name', 'care_of', 'address', 'telephone_number')

    def get_search_results(self, request, queryset, search_term):
        # Call the superclass implementation to get the initial queryset
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        if search_term:
            # Exact matches for name (highest priority)
            name_matches = queryset.filter(name__icontains=search_term)

            # Partial matches in care_of (next priority)
            care_of_matches = queryset.filter(care_of__icontains=search_term).exclude(
                pk__in=name_matches.values_list('pk', flat=True))

            address_matches = queryset.filter(address__icontains=search_term).exclude(
                pk__in=name_matches.values_list('pk', flat=True))

            telephone_matches = queryset.filter(telephone_number__icontains=search_term).exclude(
                pk__in=name_matches.values_list('pk', flat=True))

            # Combine name matches first, then care_of matches
            queryset = name_matches | care_of_matches | address_matches | telephone_matches

        return queryset, use_distinct


@admin.register(Salesman)
class SalesmanAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')

@admin.register(Deliveryman)
class DeliverymanAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity', 'price', 'unit_per_box', 'box_amount', 'box_remain')
    search_fields = ('name',)
    readonly_fields = ('box_amount', 'box_remain')  # Make box_amount and box_remain read-only

@admin.register(ProductTransaction)
class ProductTransactionAdmin(admin.ModelAdmin):
    list_display = ('product', 'transaction_type', 'change', 'quantity_after_transaction', 'timestamp', 'description')
    search_fields = ('product__name', 'transaction_type', 'description')
    list_filter = ('transaction_type', 'timestamp')

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0  # Number of extra forms to display
    readonly_fields = ('sum_price', 'price')  # Make sum_price read-only
    fields = ('product', 'quantity', 'net_price', 'price', 'sum_price', 'product_type')  # Include product_type field


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    autocomplete_fields = ['customer']
    list_display = ('number', 'terms', 'customer', 'delivery_date', 'payment_date', 'total_price')
    search_fields = ('number', 'customer__name')
    inlines = [InvoiceItemInline]
    readonly_fields = ('total_price', 'terms', 'salesman')

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.save()

    def delete_model(self, request, obj):
        """
        Override delete_model to restock products when an invoice is deleted.
        """
        for invoice_item in obj.invoiceitem_set.all():
            product = invoice_item.product
            product.quantity += invoice_item.quantity
            product.save()

            # Log the restock transaction
            if obj.delivery_date:
                ProductTransaction.objects.create(
                    product=product,
                    transaction_type='restock',
                    change=invoice_item.quantity,
                    quantity_after_transaction=product.quantity,
                    description=f"Restock due to deletion of invoice #{obj.number} from {obj.customer.name}"
                )

        # Delete the invoice
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        """
        Override delete_queryset to handle bulk deletion in the admin.
        """
        for obj in queryset:
            self.delete_model(request, obj)
