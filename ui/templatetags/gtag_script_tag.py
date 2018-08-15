from django import template
from django.conf import settings
from django.utils.html import format_html


register = template.Library()


@register.simple_tag
def gtag_script_tag():
    """
    Render Google "Global Site Tag" HTML for, e.g., Google Analytics if the GTAG_ID setting is
    present, non-None and non-empty. If the GTAG_ID setting is not present, None or empty, renders
    the empty string.

    """
    if not hasattr(settings, 'GTAG_ID'):
        return ''

    gtag_id = settings.GTAG_ID
    if gtag_id is None or gtag_id == '':
        return ''

    return format_html(r'''<!-- Global site tag (gtag.js) - Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id={gtag_id}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());

  gtag('config', '{gtag_id}');
</script>''', gtag_id=gtag_id)
