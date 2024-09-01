from django.contrib import admin
from .models import Customer, Product, Invoice, InvoiceItem

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'address')
    search_fields = ('name', 'address')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity', 'price')
    search_fields = ('name',)

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0  # Number of extra forms to display
    readonly_fields = ('sum_price', 'price')  # Make sum_price read-only
    fields = ('product', 'quantity', 'net_price', 'price', 'sum_price')  # Order of fields displayed

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('number', 'customer', 'delivery_date', 'payment_date', 'total_price')
    search_fields = ('number', 'customer__name')
    inlines = [InvoiceItemInline]
    readonly_fields = ('total_price',)
    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        # After saving related items (InvoiceItems), recalculate the total price
        form.instance.save()



# Register InvoiceItem if you want to manage it separately
@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'product', 'quantity', 'price', 'sum_price')
    search_fields = ('invoice__number', 'product__name')
    fields = ('invoice', 'product', 'quantity', 'net_price', 'sum_price')  # Order of fields displayed
    readonly_fields = ('invoice', 'product', 'quantity', 'net_price', 'sum_price')


