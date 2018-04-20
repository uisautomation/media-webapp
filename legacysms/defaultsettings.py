"""
Default settings values for the :py:mod:`legacysms` application.

"""
# Variables whose names are in upper case and do not start with an underscore from this module are
# used as default settings for the assets application. See .apps.Config how this is achieved. This
# is a bit mucky but, at the moment, Django does not have a standard way to specify default values
# for settings.  See: https://stackoverflow.com/questions/8428556/

LEGACY_SMS_REDIRECT_BASE_URL = 'https://sms.cam.ac.uk/_legacy/'
"""
Required. Base URL for redirects back to the legacy SMS. On the SMS side, Apache should be
configured to accept requests for these URLs without forwarding on to the SMS web app. This should
have the trailing slash.

"""
