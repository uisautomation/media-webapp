"""
Default settings values for the :py:mod:`smsjwplatform` application.

"""
# Variables whose names are in upper case and do not start with an underscore from this module are
# used as default settings for the smsjwplatform application. See SMSJWPlatformConfig in .apps for
# how this is achieved. This is a bit mucky but, at the moment, Django does not have a standard way
# to specify default values for settings.  See: https://stackoverflow.com/questions/8428556/

JWPLATFORM_API_KEY = ''
"""
The jwplatform API key. Defaults to the empty string but a custom system check ensures that this
setting has a non-empty value.

"""

JWPLATFORM_API_SECRET = ''
"""
The jwplatform API secret. Defaults to the empty string but a custom system check ensures that this
setting has a non-empty value.

"""

JWPLATFORM_SIGNATURE_TIMEOUT = 3600
"""
Lifetime of signed URL in seconds.

.. seealso::

    `JWPlatform documentation on URL signing
    <https://developer.jwplayer.com/jw-platform/docs/developer-guide/delivery-api/legacy-url-token-signing/>`_.

"""

JWPLATFORM_API_BASE_URL = 'https://cdn.jwplayer.com/'
"""
Base URL for the JWPlatform API. This can usually be left at its default value.

"""


JWPLATFORM_EMBED_PLAYER_KEY = ''
"""
Player key for the embedded player used by the :py:mod:`~.views.embed` view. If left blank, all
calls to :py:mod:`~smsjwplatform.views.embed` will result in a 404.

"""
