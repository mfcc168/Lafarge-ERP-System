from django import template

register = template.Library()

@register.filter(name='currency')
def currency(value):
    try:
        value = float(value)
        return f"{value:,.2f}"
    except (ValueError, TypeError):
        return value
