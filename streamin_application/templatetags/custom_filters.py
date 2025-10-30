from django import template

register = template.Library()

@register.filter
def filesizeformat(value):
    """Convert view count to K, M format"""
    try:
        value = int(value)
        if value >= 1000000:
            return f"{value/1000000:.1f}M"
        elif value >= 1000:
            return f"{value/1000:.1f}K"
        return str(value)
    except:
        return value