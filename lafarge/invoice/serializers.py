from rest_framework import serializers

from .models import *


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'


class DeliverymanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deliveryman
        fields = '__all__'


class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = '__all__'


class AdditionalItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdditionalItem
        fields = '__all__'
