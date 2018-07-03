"""
Default settings values for the :py:mod:`smsjwplatform` application.

"""
# Variables whose names are in upper case and do not start with an underscore from this module are
# used as default settings for the smsjwplatform application. See SMSJWPlatformConfig in .apps for
# how this is achieved. This is a bit mucky but, at the moment, Django does not have a standard way
# to specify default values for settings.  See: https://stackoverflow.com/questions/8428556/

JWPLATFORM_API_KEY = None
"""
The jwplatform API key. Defaults to the empty string but a custom system check ensures that this
setting has a non-empty value.

"""

JWPLATFORM_API_SECRET = None
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

JWPLATFORM_CONTENT_BASE_URL = 'https://content.jwplatform.com'
"""
Base URL for the JWPlatform Content. This can usually be left at its default value.

"""

JWPLATFORM_EMBED_PLAYER_KEY = None
"""
Player key for the embedded player used by the :py:mod:`~.views.embed` view.

"""

OAUTH2_CLIENT_ID = None
"""
OAuth2 client id which the API server uses to identify itself to the OAuth2 token introspection
endpoint.

"""

OAUTH2_CLIENT_SECRET = None
"""
OAuth2 client secret which the API server uses to identify itself to the OAuth2 token introspection
endpoint.

"""

OAUTH2_TOKEN_URL = None
"""
URL of the OAuth2 token endpoint the API server uses to request an authorisation token to perform
OAuth2 token introspection.

"""

OAUTH2_LOOKUP_SCOPES = ['lookup:anonymous']
"""
List of OAuth2 scopes the API server will request for the token it will use with lookup.

"""

OAUTH2_MAX_RETRIES = 5
"""
Maximum number of retries when fetching URLs from the OAuth2 endpoint or OAuth2 authenticated URLs.
This applies only to failed DNS lookups, socket connections and connection timeouts, never to
requests where data has made it to the server.
"""

LOOKUP_ROOT = None
"""
URL of the lookup proxy's API root.

"""

LOOKUP_PEOPLE_CACHE_LIFETIME = 1800
"""
Responses to the people endpoint of lookupproxy are cached to increase performance. We assume that
lookup details on people change rarely. This setting specifies the lifetime of a single cached
lookup resource for a person in seconds.

"""

LOOKUP_PEOPLE_ID_SCHEME = 'mock'
"""
The ID scheme to use when querying people in LOOKUP. This is almost always 'crsid' unless you are
using test raven, in which case it is 'mock'.

"""
