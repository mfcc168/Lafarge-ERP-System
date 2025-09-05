from rest_framework import status
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from django.utils.timezone import make_aware
from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from collections import defaultdict
from datetime import datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from calendar import monthrange
import re

from ..serializers import *


@api_view(['GET'])
def ProductView(request):
    """API endpoint to retrieve all products."""
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def InvoiceView(request):
    """API endpoint to retrieve all invoices."""
    invoices = Invoice.objects.all()
    serializer = InvoiceSerializer(invoices, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def CustomerView(request):
    """API endpoint to retrieve all customers."""
    customers = Customer.objects.all()
    serializer = CustomerSerializer(customers, many=True)
    return Response(serializer.data)


class UpdateDeliveryDateView(APIView):
    """API endpoint for updating invoice delivery date and deliveryman."""
    
    def patch(self, request, *args, **kwargs):
        invoice_number = request.data.get('number')
        delivery_date = request.data.get('delivery_date')
        deliveryman_name = request.data.get('deliveryman')

        deliveryman = Deliveryman.objects.get(name=deliveryman_name)

        try:
            invoice = Invoice.objects.get(number=invoice_number)
        except Invoice.DoesNotExist:
            return Response({"error": "Invoice not found"}, status=status.HTTP_404_NOT_FOUND)

        invoice.delivery_date = delivery_date
        if deliveryman:
            invoice.deliveryman = deliveryman
        invoice.save()

        # Return updated invoice data
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UpdatePaymentDateView(APIView):
    """API endpoint for updating invoice payment date."""
    
    def patch(self, request, *args, **kwargs):
        invoice_number = request.data.get('number')
        payment_date = request.data.get('payment_date')

        try:
            invoice = Invoice.objects.get(number=invoice_number)
        except Invoice.DoesNotExist:
            return Response({"error": "Invoice not found"}, status=status.HTTP_404_NOT_FOUND)

        invoice.payment_date = payment_date
        invoice.save()

        # Return updated invoice data
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data, status=status.HTTP_200_OK)


def sales_incentive_scheme(sales):
    """
    Calculate commission rate based on sales volume tiers.
    
    Args:
        sales (float): Total sales amount
        
    Returns:
        float: Commission percentage (as decimal)
    """
    if sales < 50000:
        return 0.02
    elif sales < 70000:
        return 0.025
    elif sales < 100000:
        return 0.0325
    elif sales < 130000:
        return 0.04
    elif sales < 170000:
        return 0.05
    elif sales >= 170000:
        return 0.055


class SalesmanMonthlyPreview(APIView):
    """API endpoint for salesman monthly sales summary."""
    
    def get(self, request, salesman_name):
        salesman = get_object_or_404(Salesman, name__istartswith=salesman_name.capitalize())
        latest_invoice = Invoice.objects.filter(salesman=salesman, delivery_date__isnull=False)
        latest_invoice = latest_invoice.order_by('-delivery_date').first()
        today = latest_invoice.delivery_date if latest_invoice else datetime.now().date()

        months = []
        for i in range(12):  # Process last 12 months of data
            date = today.replace(day=1) - relativedelta(months=i)
            year, month = date.year, date.month
            if year == 2025 and month == 1:
                continue
            total_amount = Invoice.objects.filter(
                salesman=salesman, delivery_date__year=year, delivery_date__month=month
            ).aggregate(total=Sum("total_price"))["total"] or 0

            if total_amount > 0:
                months.append({
                    'year': year,
                    'month': month,
                    'name': date.strftime('%B %Y'),
                    'total': total_amount,
                })

        return Response({"months": months, "salesman": salesman.name})


class SalesmanMonthlyReport(APIView):
    """API endpoint for detailed salesman monthly report with commission calculation."""
    
    def get(self, request, salesman_name, year, month):
        salesman = get_object_or_404(Salesman, name__istartswith=salesman_name.capitalize())
        sales_share1 = get_object_or_404(Salesman, name="DS/MM/AC")
        sales_share2 = get_object_or_404(Salesman, name="Kelvin Ko")
        year = int(year)
        month = int(month)

        first_day = make_aware(datetime(year, month, 1))
        last_day = make_aware(datetime(year, month, monthrange(year, month)[1]))

        invoices = Invoice.objects.filter(
            salesman=salesman, delivery_date__range=(first_day, last_day)
        ).select_related('customer', 'salesman').prefetch_related("invoiceitem_set__product")

        invoice_shares = Invoice.objects.filter(
            Q(salesman=sales_share1) | Q(salesman=sales_share2),
            delivery_date__range=(first_day, last_day)
        ).select_related('customer', 'salesman').prefetch_related("invoiceitem_set__product")

        weeks = {i: {"invoices": [], "total": Decimal("0.00")} for i in range(1, 6)}
        monthly_total = Decimal("0.00")

        for invoice in invoices:
            week_number = (invoice.delivery_date.day - 1) // 7 + 1
            if week_number > 4:
                week_number = 5

            # Group invoice items by clean product name (remove lot numbers)
            grouped_items = defaultdict(list)

            for item in invoice.invoiceitem_set.all():
                if item.product:
                    clean_name = re.sub(r"\s*\(Lot\s*no\.?:?\s*[A-Za-z0-9-]+\)", "", item.product.name)
                    grouped_items[clean_name].append(str(item.quantity))

            invoice.items = [f"{name} ({' + '.join(quantities)})" for name, quantities in grouped_items.items()]
            invoice_data = {
                'number': invoice.number,
                'customer': invoice.customer.name,
                'care_of': invoice.customer.care_of,
                'sample_customer': invoice.sample_customer,
                'salesman': invoice.salesman.name,
                'total_price': invoice.total_price,
                'delivery_date': invoice.delivery_date,
                'payment_date': invoice.payment_date,
                'items': invoice.items,
            }
            weeks[week_number]["invoices"].append(invoice_data)
            weeks[week_number]["total"] += invoice.total_price
            monthly_total += invoice.total_price

        invoice_shares_data = []
        for invoice in invoice_shares:
            # Group invoice items by clean product name (remove lot numbers)
            grouped_items = defaultdict(list)

            for item in invoice.invoiceitem_set.all():
                if item.product:
                    clean_name = re.sub(r"\s*\(Lot\s*no\.?:?\s*[A-Za-z0-9-]+\)", "", item.product.name)
                    grouped_items[clean_name].append(str(item.quantity))

            invoice.items = [f"{name} ({' + '.join(quantities)})" for name, quantities in grouped_items.items()]
            invoice_data = {
                'number': invoice.number,
                'customer': invoice.customer.name,
                'care_of': invoice.customer.care_of,
                'sample_customer': invoice.sample_customer,
                'salesman': invoice.salesman.name,
                'total_price': invoice.total_price,
                'delivery_date': invoice.delivery_date,
                'payment_date': invoice.payment_date,
                'items': invoice.items,
            }
            invoice_shares_data.append(invoice_data)

        monthly_total_share = sum(inv.total_price for inv in invoice_shares)


        commission_percentage = {"Dominic So": 0.4, "Alex Cheung": 0.3, "Matthew Mak": 0.3}.get(salesman.name, 0)
        personal_monthly_total_share = monthly_total_share * Decimal(str(commission_percentage))
        sales_monthly_total = monthly_total + personal_monthly_total_share
        incentive_percentage = sales_incentive_scheme(sales_monthly_total)
        commission = sales_monthly_total * Decimal(str(incentive_percentage)) * Decimal("1.1")

        return Response({
            "weeks": weeks,
            "year": year,
            "month": month,
            "monthly_total": monthly_total,
            "salesman": salesman.name,
            "commission": commission,
            "invoice_shares_data": invoice_shares_data,
            "monthly_total_share": monthly_total_share,
            "monthly_total_share_percentage": commission_percentage,
            "personal_monthly_total_share": personal_monthly_total_share,
            "sales_monthly_total": sales_monthly_total,
            "incentive_percentage": incentive_percentage,
        })


class GetAllSalesmenCommissions(APIView):
    """API endpoint for calculating all eligible salesmen commissions for a given month."""
    
    def get(self, request, year, month):
        year = int(year)
        month = int(month)

        first_day = make_aware(datetime(year, month, 1))
        last_day = make_aware(datetime(year, month, monthrange(year, month)[1]))

        sales_share1 = get_object_or_404(Salesman, name="DS/MM/AC")
        sales_share2 = get_object_or_404(Salesman, name="Kelvin Ko")

        # Filter to commission-eligible salesmen only
        eligible_salesmen = Salesman.objects.filter(name__in=["Dominic So", "Alex Cheung", "Matthew Mak"])

        response_data = []

        invoice_shares = Invoice.objects.filter(
            Q(salesman=sales_share1) | Q(salesman=sales_share2),
            delivery_date__range=(first_day, last_day)
        )

        monthly_total_share = sum(inv.total_price for inv in invoice_shares)


        for salesman in eligible_salesmen:
            invoices = Invoice.objects.filter(
                salesman=salesman,
                delivery_date__range=(first_day, last_day)
            )
            monthly_total = sum(inv.total_price for inv in invoices)

            commission_percentage = {
                "Dominic So": 0.4,
                "Alex Cheung": 0.3,
                "Matthew Mak": 0.3
            }.get(salesman.name, 0)

            personal_monthly_total_share = monthly_total_share * Decimal(str(commission_percentage))
            sales_monthly_total = monthly_total + personal_monthly_total_share
            incentive_percentage = sales_incentive_scheme(sales_monthly_total)
            commission = sales_monthly_total * Decimal(str(incentive_percentage)) * Decimal("1.1")

            response_data.append({
                "salesman": salesman.name,
                "commission": round(commission, 2)
            })

        return Response(response_data)
