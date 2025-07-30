import base64

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


def parse_basic_auth(auth):
    """
    Helper to parse a HTTP_AUTHORIZATION header for basic authentication

    See https://datatracker.ietf.org/doc/html/rfc7617
    """
    scheme, encoded_string = auth.split()

    if scheme.lower() != "basic":
        raise ValueError

    username, password = base64.b64decode(encoded_string).decode("utf-8").split(":", 1)

    return username, password


class BasicAuthSettingsBackend(ModelBackend):
    """
    A simple auth backend that checks that the username and password
    match the settings for basic auth. This should only be used in
    non-production environments that do not require secure authentication.
    """

    def authenticate(self, _request, username=None, password=None, **kwargs):
        if not settings.BASIC_AUTH_ENABLED:
            return None

        if (
            username == settings.BASIC_AUTH_USERNAME
            and password == settings.BASIC_AUTH_PASSWORD
        ):
            user = get_user_model().objects.filter(username=username).first()
            if self.user_can_authenticate(user):
                return user

        return None
