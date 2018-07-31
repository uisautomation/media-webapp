import json

from django import template

register = template.Library()


@register.filter
def to_json(value):
    return json.dumps(value)
