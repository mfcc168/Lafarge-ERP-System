from decimal import Decimal
from io import BytesIO
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase, override_settings
from reportlab.lib.pagesizes import A5
from reportlab.pdfgen import canvas

from ..models import Customer, Invoice, InvoiceItem, Product
from ..pdf_generation.sample import draw_sample_page


class SamplePdfTest(TestCase):
    def setUp(self):
        customer = Customer.objects.create(
            name="Sample",
            address="",
            delivery_address="",
            office_hour="",
        )
        self.invoice = Invoice.objects.create(number="S-10001", customer=customer)

    def create_product(self, name, unit):
        return Product.objects.create(name=name, unit=unit, quantity=Decimal("100.0"))

    def add_item(self, product, quantity):
        InvoiceItem.objects.create(
            invoice=self.invoice,
            product=product,
            quantity=Decimal(quantity),
            product_type="sample",
        )

    def render_table_text(self):
        pdf = canvas.Canvas(BytesIO(), pagesize=A5)
        # Render the real PDF using the source assets, without collectstatic.
        with override_settings(STATIC_ROOT=settings.BASE_DIR / "static"):
            with patch.object(pdf, "drawString", wraps=pdf.drawString) as draw_string:
                draw_sample_page(pdf, self.invoice)
                pdf.save()

        text = [call.args[2] for call in draw_string.call_args_list]
        return text[text.index("Product"):]

    def test_mixed_products_keep_their_own_quantity_units(self):
        tablets = self.create_product("Tablets (LOT 1)", "boxes")
        syrup = self.create_product("Syrup", "bottles")
        cream = self.create_product("Cream", "tubes")
        self.add_item(tablets, "2.5")
        self.add_item(syrup, "3.0")
        self.add_item(cream, "4.0")

        self.assertEqual(self.render_table_text(), [
            "Product", "Quantity",
            "Tablets (LOT 1)", "2.5 boxes",
            "Syrup", "3 bottles",
            "Cream", "4 tubes",
        ])

    def test_repeated_product_quantities_are_combined_with_the_correct_unit(self):
        tablets = self.create_product("Tablets (LOT 1)", "boxes")
        syrup = self.create_product("Syrup", "bottles")
        self.add_item(tablets, "1.2")
        self.add_item(syrup, "4.0")
        self.add_item(tablets, "2.3")

        self.assertEqual(self.render_table_text(), [
            "Product", "Quantity",
            "Tablets (LOT 1)", "3.5 boxes",
            "Syrup", "4 bottles",
        ])
