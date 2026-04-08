from django import template

register = template.Library()


@register.filter(name='smart_price')
def smart_price(value):
    """
    Format a price with comma separator ONLY if >= 1000.
    Examples:
        800   -> "800"
        1200  -> "1,200"
        12500 -> "12,500"
    """
    try:
        value = float(value)
        int_part = int(value)
        if int_part >= 1000:
            return f"{int_part:,}"
        else:
            return str(int_part)
    except (TypeError, ValueError):
        return value


@register.filter(name='baht_price')
def baht_price(value):
    """
    Format a price with baht symbol + comma if >= 1000.
    Examples:
        800   -> "800"
        1200  -> "1,200"
        12500 -> "12,500"
    (Use smart_price — adds commas only for 1000+)
    """
    try:
        value = float(value)
        int_part = int(value)
        if int_part >= 1000:
            return f"\u0e3f{int_part:,}"
        else:
            return f"\u0e3f{int_part}"
    except (TypeError, ValueError):
        return f"\u0e3f{value}"
