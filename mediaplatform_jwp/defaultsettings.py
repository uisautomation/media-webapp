"""
Default settings values for the :py:mod:`mediapltform_jwp` application.

"""
# Variables whose names are in upper case and do not start with an underscore from this module are
# used as default settings for the mediapltform_jwp application. See apps.Config for how this is
# achieved. This is a bit mucky but, at the moment, Django does not have a standard way to specify
# default values for settings. See: https://stackoverflow.com/questions/8428556/

#: Shoule matching JWP videos should be creatred/updated when MediaItem objects change.
JWP_SYNC_ITEMS = True
