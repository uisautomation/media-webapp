"""
Custom system checks for the :py:mod:`smsjwplatform` application.

.. seealso::

    The `Django System Check Framework <https://docs.djangoproject.com/en/2.0/ref/checks/>`_.

"""
from django.conf import settings
from django.core.checks import register, Error


@register
def api_credentials_check(app_configs, **kwargs):
    """
    A system check ensuring that the JWPlatform API credentials are specified.

    .. seealso:: https://docs.djangoproject.com/en/2.0/ref/checks/

    """
    # Check that all required settings are specified and non-None
    required_settings = ['JWPLATFORM_API_KEY', 'JWPLATFORM_API_SECRET']
    try:
        check_ok = all(getattr(settings, k) not in ('None', '') for k in required_settings)
    except AttributeError:
        check_ok = False

    errors = []
    if not check_ok:
        errors.append(Error(
            'JWPlatform API credentials are not set.',
            id='smsjwplatform.E001',
            hint='Add JWPLATFORM_API_KEY and JWPLATFORM_API_SECRET to settings.'))

    return errors
