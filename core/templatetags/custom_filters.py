"""
core/templatetags/custom_filters.py
Custom Django template filters needed by the system.
"""
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Access dict by key in template: {{ my_dict|get_item:key }}"""
    if isinstance(dictionary, dict):
        return dictionary.get(key, '')
    return ''


@register.filter
def split(value, delimiter=','):
    """Split a string by delimiter: {{ "a,b,c"|split:"," }}"""
    return value.split(delimiter)


@register.filter
def multiply(value, arg):
    """Multiply value by arg: {{ score|multiply:0.6 }}"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def percentage(value, total):
    """Return percentage: {{ part|percentage:total }}"""
    try:
        return round((float(value) / float(total)) * 100, 1)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def abs_val(value):
    """Return absolute value."""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return 0


@register.filter
def format_kes(value):
    """Format number as KES currency: 50000 → KES 50,000"""
    try:
        return f"KES {int(value):,}"
    except (ValueError, TypeError):
        return str(value)
