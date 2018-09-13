from django.apps import AppConfig
from django.conf import settings

from . import defaultsettings


class Config(AppConfig):
    """Configuration for JWPlatform integration application."""
    #: The short name for this application.
    name = 'mediaplatform_jwp'

    #: The human-readable verbose name for this application.
    verbose_name = 'JWPlatform Integration with Media Platform'

    def ready(self):
        """
        Perform application initialisation once the Django platform has been initialised.

        """
        # Import, and thereby register, our custom system checks
        from . import systemchecks  # noqa: F401

        # Register default settings in a rather ugly way since Django does not have a cleaner way
        # for apps to register default settings.  https://stackoverflow.com/questions/8428556/

        # Get a dictionary of settings. Only non private variables with upper case names are used.
        default_setting_values = {
            name: value for name, value in defaultsettings.__dict__.items()
            if not name.startswith('_') and name.upper() == name
        }

        # Apply this dictionary to the settings
        for name, default_value in default_setting_values.items():
            setattr(settings, name, getattr(settings, name, default_value))

        # Import, and thereby register, our custom signal handlers
        from . import signalhandlers  # noqa: F401

        # Import, and thereby register, out tasks
        from . import tasks  # noqa: F401
