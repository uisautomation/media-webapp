"""
The :py:mod:`smsjwplatform.oauth2client` module provides a wrapper around :py:class:`requests.Session`
which is pre-authorised with an OAuth2 client token.

"""
from django.conf import settings
from requests_oauthlib import OAuth2Session
from requests.adapters import HTTPAdapter
from oauthlib.oauth2 import BackendApplicationClient, TokenExpiredError


class AuthenticatedSession:
    """
    Maintain an authenticated session as a particular OAuth2 client. The client id and secret are
    specified in the :py:attr:`~smswebapp.defaultsettings.SMS_OAUTH2_CLIENT_ID` and
    :py:attr:`~smswebapp.defaultsettings.SMS_OAUTH2_CLIENT_SECRET` settings.

    :param sequence scopes: A sequence of strings specifying the scopes which should be requested
        for the token.

    """
    def __init__(self, scopes):
        self._scopes = scopes
        self._session = None

    def _get_session(self):
        """
        Get a :py:class:`requests.Session` object which is authenticated with the API application's
        OAuth2 client credentials.

        """
        client = BackendApplicationClient(client_id=settings.SMS_OAUTH2_CLIENT_ID)
        session = OAuth2Session(client=client)
        adapter = HTTPAdapter(max_retries=settings.SMS_OAUTH2_MAX_RETRIES)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        session.fetch_token(
            timeout=2, token_url=settings.SMS_OAUTH2_TOKEN_URL,
            client_id=settings.SMS_OAUTH2_CLIENT_ID,
            client_secret=settings.SMS_OAUTH2_CLIENT_SECRET,
            scope=self._scopes)
        return session

    def request(self, *args, **kwargs):
        """
        A version of :py:func:`requests.request` which is authenticated with the OAuth2 token for
        this client. If the token has timed out, it is requested again.

        """
        if self._session is None:
            self._session = self._get_session()

        try:
            return self._session.request(*args, **kwargs)
        except TokenExpiredError:
            self._session = self._get_session()
            return self._session.request(*args, **kwargs)
