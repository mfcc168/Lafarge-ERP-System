from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

class Customer(models.Model):
    name = models.CharField(max_length=255)
    care_of = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField()
    office_hour = models.TextField(blank=True, null=True)
    telephone_number = models.CharField(max_length=255, blank=True, null=True)
    contact_person = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

class Salesman(models.Model):
    code = models.CharField(max_length=255)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.code

class Deliveryman(models.Model):
    code = models.CharField(max_length=255)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.code

class Product(models.Model):
    name = models.CharField(max_length=255)
    unit = models.CharField(max_length=255, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    quantity = models.PositiveIntegerField(default=0)
    unit_per_box = models.PositiveIntegerField(default=1)  # New field
    box_amount = models.PositiveIntegerField(default=0, editable=False)  # New field
    box_remain = models.PositiveIntegerField(default=0, editable=False)  # New field

    def save(self, *args, **kwargs):
        # Calculate box_amount and box_remain based on the quantity and unit_per_box
        if self.unit_per_box > 0:
            self.box_amount, self.box_remain = divmod(self.quantity, self.unit_per_box)
        else:
            self.box_amount, self.box_remain = 0, self.quantity

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

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
    salesman = models.ForeignKey(Salesman, on_delete=models.CASCADE)
    delivery_date = models.DateField(null=True, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    products = models.ManyToManyField(Product, through='InvoiceItem')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def calculate_total_price(self):
        total = sum(item.sum_price for item in self.invoiceitem_set.all())
        self.total_price = total

    def save(self, *args, **kwargs):
        self.calculate_total_price()  # Calculate total before saving
        super().save(*args, **kwargs)

    def __str__(self):
        return self.number


class InvoiceItem(models.Model):
    PRODUCT_TYPE_CHOICES = [
        ('normal', 'Normal'),
        ('sample', 'Sample'),
        ('bonus', 'Bonus'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    net_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sum_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    product_type = models.CharField(max_length=10, choices=PRODUCT_TYPE_CHOICES, default='normal')

    def save(self, *args, **kwargs):
        if self.pk:  # Existing record
            previous = InvoiceItem.objects.get(pk=self.pk)
            if previous.quantity != self.quantity:
                # Calculate change in quantity
                change = self.quantity - previous.quantity

                # Adjust product quantity based on product type
                if previous.product_type:
                    self.product.quantity += previous.quantity  # Restore previous quantity
                if self.product_type:
                    self.product.quantity -= self.quantity  # Deduct new quantity

                # Log the product transaction
                ProductTransaction.objects.create(
                    product=self.product,
                    transaction_type='sale' if self.product_type == 'normal' else 'adjustment',
                    change=-change,
                    quantity_after_transaction=self.product.quantity,
                    description=f"{self.product_type.capitalize()} transaction in invoice #{self.invoice.number}"
                )

        else:  # New record
            # Adjust product quantity based on product type
            if self.product_type:
                self.product.quantity -= self.quantity

            # Log transaction for new item
            ProductTransaction.objects.create(
                product=self.product,
                transaction_type='sale',
                change=-self.quantity,
                quantity_after_transaction=self.product.quantity,
                description=f"{self.product_type.capitalize()} in invoice {self.invoice.number}"
            )

        # Save product and the invoice item
        self.product.save()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # For deletion, always restock
        self.product.quantity += self.quantity
        self.product.save()

        # Log restock transaction
        ProductTransaction.objects.create(
            product=self.product,
            transaction_type='restock',
            change=self.quantity,
            quantity_after_transaction=self.product.quantity,
            description=f"Restock due to deletion of {self.product_type} invoice item {self.invoice.number}"
        )

        super().delete(*args, **kwargs)


# Signals to update total price
@receiver(post_save, sender=InvoiceItem)
def update_invoice_total(sender, instance, **kwargs):
    instance.invoice.calculate_total_price()
    instance.invoice.save()

@receiver(post_delete, sender=InvoiceItem)
def revert_invoice_total(sender, instance, **kwargs):
    instance.invoice.calculate_total_price()
    instance.invoice.save()
