"""Django REST Framework serializers for the invoice application."""

from rest_framework import serializers

from .models import *


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model."""
    class Meta:
        model = Product
        fields = '__all__'


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for Invoice model."""
    class Meta:
        model = Invoice
        fields = '__all__'


class CustomerSerializer(serializers.ModelSerializer):
    """Serializer for Customer model."""
    class Meta:
        model = Customer
        fields = '__all__'


class DeliverymanSerializer(serializers.ModelSerializer):
    """Serializer for Deliveryman model."""
    class Meta:
        model = Deliveryman
        fields = '__all__'


class InvoiceItemSerializer(serializers.ModelSerializer):
    """Serializer for InvoiceItem model."""
    class Meta:
        model = InvoiceItem
        fields = '__all__'


class AdditionalItemSerializer(serializers.ModelSerializer):
    """Serializer for AdditionalItem model."""
    class Meta:
        model = AdditionalItem
        fields = '__all__'
