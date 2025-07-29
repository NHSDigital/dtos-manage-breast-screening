from base64 import b64encode

import pytest
from django.contrib.auth import get_user_model


@pytest.fixture
def user():
    return get_user_model().objects.create_user(
        email="test@example.com", username="testusername"
    )


@pytest.fixture
def set_basic_auth_credentials(settings, user):
    settings.BASIC_AUTH_ENABLED = True
    settings.BASIC_AUTH_USERNAME = "testusername"
    settings.BASIC_AUTH_PASSWORD = "testpassword"
    settings.AUTHENTICATION_BACKENDS = [
        "manage_breast_screening.core.utils.auth.BasicAuthSettingsBackend"
    ]


@pytest.fixture
def basic_auth_valid_authorization_token():
    encoded = b64encode(b"testusername:testpassword").decode()
    return f"Basic {encoded}"
