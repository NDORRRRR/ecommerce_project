from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """Multiply the arg and the value."""
    return int(value) * int(arg)