from django.apps import AppConfig


class Config(AppConfig):
    """Configuration for OAI-PMH application."""
    #: The short name for this application.
    name = 'oaipmh'

    #: The human-readable verbose name for this application.
    verbose_name = 'OAI-PMH harvesting'
