from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers import *


@api_view(['GET'])
def ProductView(request):
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def InvoiceView(request):
    invoices = Invoice.objects.all()
    serializer = InvoiceSerializer(invoices, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def CustomerView(request):
    customers = Customer.objects.all()
    serializer = CustomerSerializer(customers, many=True)
    return Response(serializer.data)


class UpdateDeliveryDateView(APIView):
    def patch(self, request, *args, **kwargs):
        invoice_number = request.data.get('number')
        delivery_date = request.data.get('delivery_date')
        deliveryman_name = request.data.get('deliveryman')

        deliveryman = Deliveryman.objects.get(name=deliveryman_name)

        try:
            invoice = Invoice.objects.get(number=invoice_number)
        except Invoice.DoesNotExist:
            return Response({"error": "Invoice not found"}, status=status.HTTP_404_NOT_FOUND)

        # Update the delivery_date
        invoice.delivery_date = delivery_date
        # Update the deliveryman is not null
        if deliveryman:
            invoice.deliveryman = deliveryman
        invoice.save()

        # Serialize the updated invoice and return the response
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UpdatePaymentDateView(APIView):
    def patch(self, request, *args, **kwargs):
        invoice_number = request.data.get('number')
        payment_date = request.data.get('payment_date')

        try:
            invoice = Invoice.objects.get(number=invoice_number)
        except Invoice.DoesNotExist:
            return Response({"error": "Invoice not found"}, status=status.HTTP_404_NOT_FOUND)

        # Update the delivery_date
        invoice.payment_date = payment_date
        invoice.save()

        # Serialize the updated invoice and return the response
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data, status=status.HTTP_200_OK)
