import base64

import pytest
from django.contrib.auth import get_user_model

from manage_breast_screening.core.utils.auth import (
    BasicAuthSettingsBackend,
    parse_basic_auth,
)


class TestParseBasicAuth:
    def test_valid(self):
        assert parse_basic_auth("Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ==") == (
            "Aladdin",
            "open sesame",
        )

    def test_invalid_scheme(self):
        with pytest.raises(ValueError):
            parse_basic_auth("Another QWxhZGRpbjpvcGVuIHNlc2FtZQ==")

    def test_invalid_base64(self):
        with pytest.raises(ValueError):
            parse_basic_auth("Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ=")

    def test_invalid_encoded_contents(self):
        encoded = base64.b64encode(b"opensesame")

        with pytest.raises(ValueError):
            parse_basic_auth(f"Basic {encoded}")


@pytest.mark.django_db
class TestBasicAuthSettingsBackend:
    @pytest.fixture
    def user(self):
        return get_user_model().objects.create_user(
            email="test@example.com", username="testusername"
        )

    @pytest.fixture(autouse=True)
    def setup(self, settings, user):
        settings.BASIC_AUTH_ENABLED = True
        settings.BASIC_AUTH_USERNAME = "testusername"
        settings.BASIC_AUTH_PASSWORD = "testpassword"

    def test_authenticate_invalid_credentials(self, settings):
        backend = BasicAuthSettingsBackend()

        result = backend.authenticate(None, username="testusername", password="wrong")
        assert result is None

    def test_authenticate_valid_credentials(self, user, settings):
        backend = BasicAuthSettingsBackend()

        result = backend.authenticate(
            None, username="testusername", password="testpassword"
        )
        assert result == user

    def test_authenticate_with_user_record_missing(self, user, settings):
        settings.BASIC_AUTH_USERNAME = "missinguser"

        backend = BasicAuthSettingsBackend()

        result = backend.authenticate(
            None, username="missinguser", password="testpassword"
        )
        assert result is None

    def test_authenticate_with_basic_auth_disabled(self, user, settings):
        settings.BASIC_AUTH_ENABLED = False

        backend = BasicAuthSettingsBackend()

        result = backend.authenticate(
            None, username="testusername", password="testpassword"
        )
        assert result is None

    def test_authenticate_with_inactive_user(self, user):
        user.is_active = False
        user.save()

        backend = BasicAuthSettingsBackend()

        result = backend.authenticate(
            None, username="testusername", password="testpassword"
        )
        assert result is None
