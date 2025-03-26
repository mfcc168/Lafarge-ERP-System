from django import template
from decimal import Decimal, ROUND_UP

register = template.Library()


@register.filter(name='currency')
def currency(value):
    try:
        value = float(value)
        return f"{value:,.2f}"
    except (ValueError, TypeError):
        return value


@register.filter(name='item')
def item(value):
    try:
        value = float(value)
        return f"{value:,.1f}"
    except (ValueError, TypeError):
        return value

@register.filter(name='unit_price')
def unit_price(item):
    if item.product.units_per_pack > 0:
        return f"{(item.price / item.product.units_per_pack).quantize(Decimal('0.01'), rounding=ROUND_UP):,.2f}"
    return 0