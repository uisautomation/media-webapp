"""
Views specific to SMS web application.

"""
from django.shortcuts import render


def index(request):
    """Placeholder index view which renders the smswebapp/index.html template."""
    return render(request, 'smswebapp/index.html')
