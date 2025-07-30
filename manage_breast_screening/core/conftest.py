from base64 import b64encode

import pytest


@pytest.fixture
def set_basic_auth_credentials(settings, user):
    settings.BASIC_AUTH_ENABLED = True
    settings.BASIC_AUTH_USERNAME = "testusername"
    settings.BASIC_AUTH_PASSWORD = "testpassword"


@pytest.fixture
def basic_auth_valid_authorization_token():
    encoded = b64encode(b"testusername:testpassword").decode()
    return f"Basic {encoded}"
