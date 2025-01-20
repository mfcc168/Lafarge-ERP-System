from django.db import models, transaction
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from datetime import timedelta, date
from django.db.models import Q

class Salesman(models.Model):
    code = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.code

class Customer(models.Model):
    name = models.CharField(max_length=255, unique=True)
    care_of = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField()
    terms = models.CharField(max_length=50, null=True, blank=True)
    office_hour = models.TextField(blank=True, null=True)
    telephone_number = models.CharField(max_length=255, blank=True, null=True)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    delivery_to = models.CharField(max_length=255, blank=True, null=True)
    delivery_address = models.TextField(blank=True, null=True)
    show_registration_code = models.BooleanField(default=False)
    show_expiry_date = models.BooleanField(default=False)
    salesman = models.ForeignKey(Salesman, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name + (" ("+self.care_of+")" if self.care_of else "")



class Deliveryman(models.Model):
    code = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.code

class Product(models.Model):
    name = models.CharField(max_length=255, unique=True)
    registration_code = models.CharField(max_length=255, blank=True, null=True)
    expiry_date = models.DateField(null=True, blank=True)
    unit = models.CharField(max_length=255, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    quantity = models.PositiveIntegerField(default=0)
    unit_per_box = models.PositiveIntegerField(default=1)
    box_amount = models.PositiveIntegerField(default=0, editable=False)
    box_remain = models.PositiveIntegerField(default=0, editable=False)

    def save(self, *args, **kwargs):
        # Calculate box_amount and box_remain based on the quantity and unit_per_box
        if self.unit_per_box > 0:
            self.box_amount, self.box_remain = divmod(self.quantity, self.unit_per_box)
        else:
            self.box_amount, self.box_remain = 0, self.quantity

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name + " (Quantity: " + str(self.quantity) +")"

class ProductTransaction(models.Model):
    TRANSACTION_CHOICES = [
        ('sale', 'Sale'),
        ('restock', 'Restock'),
        ('adjustment', 'Adjustment'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_CHOICES)
    change = models.IntegerField()  # Positive for restock, negative for sale
    quantity_after_transaction = models.PositiveIntegerField()
    timestamp = models.DateTimeField(default=timezone.now)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.product.name} - {self.transaction_type} ({self.change}) on {self.timestamp}"

class Invoice(models.Model):
    number = models.CharField(max_length=50, unique=True)
    terms = models.CharField(max_length=50, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    salesman = models.ForeignKey(Salesman, on_delete=models.CASCADE, null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    products = models.ManyToManyField(Product, through='InvoiceItem')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    order_number = models.CharField(max_length=50, null=True, blank=True)

    @staticmethod
    def get_unpaid_invoices():
        today = timezone.now().date()
        first_of_this_month = today.replace(day=1)
        last_month = first_of_this_month - timedelta(days=1)
        first_of_last_month = last_month.replace(day=1)

        threshold_date = today - timedelta(days=30)

        return Invoice.objects.filter(
            Q(payment_date__isnull=True) & (
                Q(delivery_date__lte=threshold_date) |
                Q(delivery_date__gte=first_of_last_month, delivery_date__lte=last_month)
            )
        )

    def calculate_total_price(self):
        total = round(sum(item.sum_price for item in self.invoiceitem_set.all()))
        self.total_price = total

    def save(self, *args, **kwargs):
        # Automatically set salesman from customer if not already set
        if not self.salesman and self.customer.salesman:
            self.salesman = self.customer.salesman
        # Automatically set terms from customer if not already set
        if not self.terms and self.customer.terms:
            self.terms = self.customer.terms

        is_new = self.pk is None
        previous_delivery_date = None

        if not is_new or self.pk:
            # Get the previous state of the invoice
            previous_delivery_date = Invoice.objects.get(pk=self.pk).delivery_date
            # Calculate the total price after saving (whether it's new or existing)
            self.calculate_total_price()

        super().save(*args, **kwargs)

        if not previous_delivery_date and self.delivery_date:
            # Create ProductTransaction records for related items
            for item in self.invoiceitem_set.all():
                product = item.product
                ProductTransaction.objects.create(
                    product=product,
                    transaction_type='sale',
                    change=-item.quantity,
                    quantity_after_transaction=product.quantity,
                    description=f"{item.product_type.capitalize()} transaction in invoice #{self.number} from {self.customer.name}",
                    timestamp=self.delivery_date
                )



class InvoiceItem(models.Model):
    PRODUCT_TYPE_CHOICES = [
        ('normal', 'Normal'),
        ('bonus', 'Bonus'),
        ('sample', 'Sample'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    net_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sum_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    product_type = models.CharField(max_length=10, choices=PRODUCT_TYPE_CHOICES, default='normal')

    def save(self, *args, **kwargs):
        with transaction.atomic():
            # Determine if this is an update or a new item
            is_edit = self.pk is not None
            current_product = Product.objects.get(pk=self.product.pk)

            if is_edit:
                # If it's an edit, get the previous item to revert its quantity
                previous_item = InvoiceItem.objects.get(pk=self.pk)
                previous_quantity = previous_item.quantity

                # Revert the previous quantity back to the product
                current_product.quantity += previous_quantity

            # Calculate new quantity
            new_quantity = current_product.quantity - self.quantity

            # Update the product quantity
            current_product.quantity = new_quantity

            # Calculate price details
            if self.product_type == 'normal':
                self.price = current_product.price if not self.net_price else self.net_price
                self.sum_price = round(self.price * self.quantity)
            else:
                self.sum_price = 0.00  # For sample and bonus types

            # Save the updated product quantity
            current_product.save()
            # Finally, save the invoice item
            super().save(*args, **kwargs)


# Signals to update total price
@receiver(post_save, sender=InvoiceItem)
def update_invoice_total(sender, instance, **kwargs):
    instance.invoice.calculate_total_price()
    instance.invoice.save()


@receiver(post_delete, sender=InvoiceItem)
def revert_invoice_total(sender, instance, **kwargs):
    instance.invoice.calculate_total_price()
    instance.invoice.save()
