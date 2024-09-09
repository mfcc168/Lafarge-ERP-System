from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

class Customer(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    available_from = models.CharField(max_length=255, blank=True, null=True)
    available_to = models.CharField(max_length=255, blank=True, null=True)

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
        super().save(*args, **kwargs)
        self.calculate_total_price()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.number

class InvoiceItem(models.Model):
    INVOICE_TYPE_CHOICES = [
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
    invoice_type = models.CharField(max_length=10, choices=INVOICE_TYPE_CHOICES, default='normal')

    def save(self, *args, **kwargs):
        if self.invoice_type == 'normal':
            if not self.net_price:
                self.price = self.product.price
            self.sum_price = self.price * self.quantity
        else:
            # For 'sample' and 'bonus' types, the sum_price is zero
            self.sum_price = 0.00

        # Update product inventory for all invoice types
        if self.pk:  # Existing record, update inventory
            previous = InvoiceItem.objects.get(pk=self.pk)
            delta = self.quantity - previous.quantity
        else:  # New record
            delta = -self.quantity

        self.product.quantity += delta
        self.product.save()

        # Log the transaction
        ProductTransaction.objects.create(
            product=self.product,
            transaction_type='sale' if self.invoice_type == 'normal' else 'adjustment',
            change=-delta,
            quantity_after_transaction=self.product.quantity,
            description=f"{self.invoice_type.capitalize()} in invoice {self.invoice.number}"
        )

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.product.quantity += self.quantity
        self.product.save()

        # Log the transaction
        ProductTransaction.objects.create(
            product=self.product,
            transaction_type='adjustment',
            change=self.quantity,
            quantity_after_transaction=self.product.quantity,
            description=f"Deletion of {self.invoice_type} invoice item {self.invoice.number}"
        )

        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Invoice {self.invoice.number} - {self.product.name} ({self.quantity} @ {self.price})"



# Signals to update total price
@receiver(post_save, sender=InvoiceItem)
def update_invoice_total(sender, instance, **kwargs):
    instance.invoice.calculate_total_price()
    instance.invoice.save()

@receiver(post_delete, sender=InvoiceItem)
def revert_invoice_total(sender, instance, **kwargs):
    instance.invoice.calculate_total_price()
    instance.invoice.save()
