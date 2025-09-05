from django import forms
from .models import SpecialPrice, Product, extract_base_name


class SpecialPriceInlineForm(forms.ModelForm):
    """Form for managing customer-specific product pricing."""
    product_base_name = forms.ChoiceField(choices=[])

    class Meta:
        model = SpecialPrice
        fields = ['product_base_name', 'special_price']

    def __init__(self, *args, **kwargs):
        """Initialize form with available product base names."""
        super().__init__(*args, **kwargs)
        product_names = Product.objects.values_list('name', flat=True)
        base_names = sorted(set(extract_base_name(name) for name in product_names))
        self.fields['product_base_name'].choices = [(name, name) for name in base_names]