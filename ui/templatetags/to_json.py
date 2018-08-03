import json

from django import template
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()


_json_script_escapes = {
    ord('>'): '\\u003E',
    ord('<'): '\\u003C',
    ord('&'): '\\u0026',
}


@register.filter
def to_json(value):
    """
    Encode a value to JSON using the DjangoJSONEncoder. Escape all the HTML/XML special characters
    with their unicode escapes, so value is safe to be output anywhere except for inside a tag
    attribute.

    See: https://docs.djangoproject.com/en/2.1/topics/serialization/#serialization-formats-json
    See: django.utils.html.json_script

    """
    json_str = json.dumps(value, cls=DjangoJSONEncoder).translate(_json_script_escapes)
    return format_html('{}', mark_safe(json_str))
