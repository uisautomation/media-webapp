"""
Sickle client integration for repositories.

"""
from sickle import Sickle


def client_for_repository(repository):
    """
    Return a sickle client object pre-configured for the passed repository.

    """
    # Extra arguments to the Sickle constructor
    client_args = {}

    # If there is a basic auth configuration, add it to the client args
    if repository.basic_auth_user != '':
        client_args['auth'] = (repository.basic_auth_user, repository.basic_auth_password)

    # Construct client object
    return Sickle(repository.url, **client_args)
