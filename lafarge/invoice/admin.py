from django.contrib import admin
from django.db.models import Case, When, Value, IntegerField
from django.urls import path, reverse
from django.http import HttpResponseRedirect
from django.utils.html import format_html
from .models import SpecialPrice
from .forms import SpecialPriceInlineForm

from .models import Customer, Salesman, Deliveryman, Invoice, InvoiceItem, Product, ProductTransaction, Forbidden_Word, AdditionalItem

admin.site.site_header = "Lafarge Admin"
admin.site.site_title = "Lafarge Admin Portal"
admin.site.index_title = "Welcome to Lafarge Admin Panel"


class SpecialPriceInline(admin.TabularInline):
    model = SpecialPrice
    form = SpecialPriceInlineForm
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'care_of', 'address', 'telephone_number')
    search_fields = ('name', 'care_of', 'address', 'telephone_number')
    inlines = [SpecialPriceInline]
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


@admin.register(Forbidden_Word)
class Forbidden_WordAdmin(admin.ModelAdmin):
    list_display = ('word',)


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
    list_display = ('name', 'quantity', 'price', 'unit_per_box', 'box_amount', 'box_remain', 'copy_product_button')
    search_fields = ('name',)
    readonly_fields = ('box_amount', 'box_remain')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('copy/<int:product_id>/', self.admin_site.admin_view(self.copy_product), name='invoice_product_copy'),
        ]
        return custom_urls + urls

    def copy_product(self, request, product_id):
        original = Product.objects.get(pk=product_id)
        params = {
            'name': original.name,
            'supplier': original.supplier if original.supplier else '',
            'import_date': original.import_date if original.import_date else '',
            'registration_code': original.registration_code if original.registration_code else '',
            'unit': original.unit,
            'price': original.price,
            'units_per_pack': original.units_per_pack,
        }
        base_url = reverse('admin:invoice_product_add')
        query_string = "&".join(f"{key}={value}" for key, value in params.items())
        return HttpResponseRedirect(f"{base_url}?{query_string}")

    def copy_product_button(self, obj):
        url = reverse('admin:invoice_product_copy', args=[obj.pk])
        return format_html('<a class="button" href="{}">Copy</a>', url)

    copy_product_button.short_description = 'Copy Product'


@admin.register(ProductTransaction)
class ProductTransactionAdmin(admin.ModelAdmin):
    list_display = ('product', 'transaction_type', 'change', 'quantity_after_transaction', 'timestamp', 'description')
    search_fields = ('product__name', 'transaction_type', 'description')
    list_filter = ('transaction_type', 'timestamp')


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0  # Number of extra forms to display
    readonly_fields = ('sum_price', 'price')  # Make sum_price read-only
    fields = (
        'product', 'quantity', 'net_price', 'hide_nett', 'price', 'sum_price',
        'product_type')  # Include product_type field

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "product":
            # Get all products and split them into two groups
            products_gt_zero = Product.objects.filter(quantity__gt=0).order_by('name')
            products_eq_zero = Product.objects.filter(quantity=0).order_by('name')

            # Combine the two querysets and annotate them for sorting
            combined_queryset = (products_gt_zero | products_eq_zero).annotate(
                sort_order=Case(
                    When(quantity=0, then=Value(1)),  # Products with quantity = 0 get a higher sort order
                    default=Value(0),  # Products with quantity > 0 get a lower sort order
                    output_field=IntegerField(),
                )
            ).order_by('sort_order', 'name')  # Sort by sort_order first, then by name

            # Set the combined queryset as the queryset for the product field
            kwargs["queryset"] = combined_queryset

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class AdditionalItemInline(admin.TabularInline):
    model = AdditionalItem
    extra = 0
    fields = ('description', 'price')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    autocomplete_fields = ['customer']
    list_display = ('number', 'terms', 'customer', 'delivery_date', 'payment_date', 'total_price', 'view_invoice_link')
    search_fields = ('number', 'customer__name')
    inlines = [InvoiceItemInline, AdditionalItemInline]
    readonly_fields = ('total_price', 'terms', 'salesman')

    def view_invoice_link(self, obj):
        url = reverse('invoice_detail', kwargs={'invoice_number': obj.number})
        return format_html('<a class="button" href="{}" target="_blank">View Invoice</a>', url)

    view_invoice_link.short_description = "Invoice Page"

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
