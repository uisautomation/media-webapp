"""
Custom system checks for the :py:mod:`mediaplatform_jwp` application.

.. seealso::

    The `Django System Check Framework <https://docs.djangoproject.com/en/2.0/ref/checks/>`_.

"""
from django.conf import settings
from django.core.checks import register, Error


@register
def required_settings_check(app_configs, **kwargs):
    """
    A system check ensuring that all required settings are specified.

    .. seealso:: https://docs.djangoproject.com/en/2.0/ref/checks/

    """
    # Check that all required settings are specified and non-None
    required_settings = [
        'JWPLATFORM_API_KEY',
        'JWPLATFORM_API_SECRET',
        'JWPLATFORM_EMBED_PLAYER_KEY',
        'OAUTH2_CLIENT_ID',
        'OAUTH2_CLIENT_SECRET',
        'OAUTH2_TOKEN_URL',
        'LOOKUP_ROOT',
    ]

    errors = []

    for idx, name in enumerate(required_settings):
        value = getattr(settings, name, None)
        if value is None or value == '':
            errors.append(Error(
                'Required setting {} not set'.format(name),
                id='assets.E{:03d}'.format(idx + 1),
                hint='Add {} to settings.'.format(name)))

    return errors
