from django.test import TestCase
from ..models import Customer, Invoice
from ..number_generation_utils import generate_next_number, extract_number


# RUN TEST WITH THIS COMMAND python manage.py test invoice.tests.test_number_generation

class ExtractNumberTest(TestCase):
    def test_extract_number1(self):
        result = extract_number("34083 DS")
        self.assertEqual(str(result), "34083")

    def test_extract_number2(self):
        result = extract_number("34083")
        self.assertEqual(str(result), "34083")


class GenerateNextNumberTest(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(name="Test Customer")

    def test_generate_next_number1(self):
        Invoice.objects.create(number="34963", customer=self.customer)
        Invoice.objects.create(number="34983", customer=self.customer)

        result = generate_next_number()

        self.assertEqual(result, "34984")

    def test_generate_next_number2(self):
        Invoice.objects.create(number="34963 DS", customer=self.customer)
        Invoice.objects.create(number="34983 DS", customer=self.customer)

        result = generate_next_number()

        self.assertEqual(result, "34984")

    def test_generate_next_number3(self):
        Invoice.objects.create(number="34963 (DS)", customer=self.customer)
        Invoice.objects.create(number="34983 (DS)", customer=self.customer)

        result = generate_next_number()

        self.assertEqual(result, "34984")

    def test_generate_next_number4(self):
        Invoice.objects.create(number="S-34963 (DS)", customer=self.customer)
        Invoice.objects.create(number="S-34983 (DS)", customer=self.customer)

        result = generate_next_number()

        self.assertEqual(result, "34984")
