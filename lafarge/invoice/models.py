from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

class Customer(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    available_from = models.TimeField(blank=True, null=True)
    available_to = models.TimeField(blank=True, null=True)

    def __str__(self):
        return self.name

class Salesman(models.Model):
    code = models.CharField(max_length=255)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.code

class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    quantity = models.PositiveIntegerField(default=0)  # Changed to PositiveIntegerField

    def __str__(self):
        return self.name

class Invoice(models.Model):
    number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    salesman = models.ForeignKey(Salesman, on_delete=models.CASCADE)
    delivery_date = models.DateField(null=True, blank=True)  # Optional field
    payment_date = models.DateField(null=True, blank=True)    # Optional field
    products = models.ManyToManyField(Product, through='InvoiceItem')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def calculate_total_price(self):
        total = sum(item.sum_price for item in self.invoiceitem_set.all())
        self.total_price = total

    def save(self, *args, **kwargs):
        # First, save the invoice to ensure it has a primary key
        super().save(*args, **kwargs)

        # Now calculate and update the total price
        self.calculate_total_price()

        # Save again to update the total price
        super().save(*args, **kwargs)

    def __str__(self):
        return self.number

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    net_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sum_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        # If the net price has not been manually set, use the product's price
        if not self.net_price:
            self.price = self.product.price

        # Calculate sum_price based on the price and quantity
        self.sum_price = self.price * self.quantity

        # Update product inventory
        if self.pk:  # Existing record, update inventory
            previous = InvoiceItem.objects.get(pk=self.pk)
            delta = self.quantity - previous.quantity
            self.product.quantity -= delta
        else:  # New record
            self.product.quantity -= self.quantity

        self.product.save()

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Restore inventory when an InvoiceItem is deleted
        self.product.quantity += self.quantity
        self.product.save()
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Invoice {self.invoice.number} - {self.product.name} ({self.quantity} @ {self.price})"

# Optional: Signals to handle related operations
@receiver(post_save, sender=InvoiceItem)
def update_invoice_total(sender, instance, **kwargs):
    instance.invoice.calculate_total_price()
    instance.invoice.save()

@receiver(post_delete, sender=InvoiceItem)
def revert_invoice_total(sender, instance, **kwargs):
    instance.invoice.calculate_total_price()
    instance.invoice.save()
