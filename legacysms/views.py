"""
Views for Support for Legacy SMS

"""

import datetime
from django.http import HttpResponse


# Create your views here.
def example(request):
    """
    A simple example view which renders the current date and time.

    """
    now = datetime.datetime.now()
    html = "<html><body>It is now %s.</body></html>" % now
    return HttpResponse(html)
