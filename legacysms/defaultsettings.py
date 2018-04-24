"""
Default settings values for the :py:mod:`legacysms` application.

"""
# Variables whose names are in upper case and do not start with an underscore from this module are
# used as default settings for the assets application. See .apps.Config how this is achieved. This
# is a bit mucky but, at the moment, Django does not have a standard way to specify default values
# for settings.  See: https://stackoverflow.com/questions/8428556/

LEGACY_SMS_REDIRECT_FORMAT = '{url.scheme}://{url.netloc}/_legacy{url.path}'
"""
Required. Format string for generating URL used when redirecting a request back to the legacy SMS.
The format string should use a named parameter called *url* which is an instance of the tuple
subclass returned by calling :py:func:`urllib.parse.urlsplit` on the original SMS URL. On the SMS
side, Apache should be configured to accept requests for these URLs without forwarding on to the
SMS web app.

"""

LEGACY_SMS_FRONTEND_URL = 'https://sms.cam.ac.uk/'
"""
Required. URL of legacy SMS web frontend.

"""

LEGACY_SMS_RSS_URL = 'https://rss.sms.cam.ac.uk/'
"""
Required. URL of legacy SMS RSS feed site.

"""

LEGACY_SMS_DOWNLOADS_URL = 'https://downloads.sms.cam.ac.uk/'
"""
Required. URL of legacy SMS download site.

"""
