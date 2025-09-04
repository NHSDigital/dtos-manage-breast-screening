import time

import requests_mock
from authlib.jose import JsonWebKey, jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test.client import Client as TestClient
from django.urls import reverse
from playwright.sync_api import expect

from .system_test_setup import SystemTestCase


class TestCIS2BackChannelLogout(SystemTestCase):
    """
    System test for CIS2 back-channel logout endpoint. This test uses an
    actual instance of our CIS2 OAuth client (instantiated with test settings),
    and mocks calls to the CIS2 server metadata and JWKS endpoints.
    """

    def test_back_channel_logout_invalidates_user_sessions(self):
        self.given_i_am_signed_in()
        self.and_cis2_has_a_key_pair()
        self.and_the_cis2_jwks_endpoint_is_setup()
        self.and_there_is_a_cis2_logout_token()
        self.when_the_back_channel_logout_endpoint_is_called()
        self.then_i_am_logged_out()

    def test_back_channel_logout_with_expired_token_is_rejected(self):
        self.given_i_am_signed_in()
        self.and_cis2_has_a_key_pair()
        self.and_the_cis2_jwks_endpoint_is_setup()
        self.and_there_is_an_expired_cis2_logout_token()
        self.when_the_back_channel_logout_endpoint_is_called()
        self.then_the_request_is_rejected_and_i_remain_logged_in()

    def given_i_am_signed_in(self):
        User = get_user_model()
        self.user_id = "user-123"
        user = User.objects.create_user(username=self.user_id, password="irrelevant")

        self.login_as_user(user)
        self.page.goto(self.live_server_url + reverse("clinics:index"))
        header = self.page.get_by_role("navigation")
        expect(header.get_by_text("Log out")).to_be_visible()

    def and_cis2_has_a_key_pair(self):
        self.cis2_key_id = "key1"
        self.cis2_jwk = JsonWebKey.generate_key(
            "RSA", 2048, is_private=True, options={"kid": self.cis2_key_id}
        )

    def and_the_cis2_jwks_endpoint_is_setup(self):
        self._requests_mocker = requests_mock.Mocker()
        self._requests_mocker.start()
        self.addCleanup(self._requests_mocker.stop)

        metadata_url = settings.CIS2_SERVER_METADATA_URL
        self.issuer = "test-issuer"
        jwks_url = "http://example.com/test/oidc/jwks"
        self._requests_mocker.get(
            metadata_url,
            json={"issuer": self.issuer, "jwks_uri": jwks_url},
            status_code=200,
        )

        public_jwk = self.cis2_jwk.as_dict(is_private=False)
        self._requests_mocker.get(
            jwks_url,
            json={"keys": [public_jwk]},
            status_code=200,
        )

    def and_there_is_a_cis2_logout_token(self):
        self.token = self._create_logout_token()

    def and_there_is_an_expired_cis2_logout_token(self):
        now = int(time.time())
        self.token = self._create_logout_token(
            {
                "iat": now - 300,
                "exp": now - 120,  # expired beyond leeway used in service
            }
        )

    def when_the_back_channel_logout_endpoint_is_called(self):
        client = TestClient()
        url = reverse("auth:cis2_back_channel_logout")
        self.response = client.post(url, data={"logout_token": self.token})

    def then_i_am_logged_out(self):
        assert self.response.status_code == 200

        User = get_user_model()
        user = User.objects.get(username=self.user_id)
        assert user.session_set.all().count() == 0

        self.page.goto(self.live_server_url + reverse("home"))
        header = self.page.get_by_role("navigation")
        expect(header.get_by_text("Log in")).to_be_visible()

    def then_the_request_is_rejected_and_i_remain_logged_in(self):
        # The view should reject expired tokens
        assert self.response.status_code == 400

        # Session for the user should still exist
        User = get_user_model()
        user = User.objects.get(username=self.user_id)
        assert user.session_set.all().count() == 1

        # UI should still show user as logged in
        self.page.goto(self.live_server_url + reverse("home"))
        header = self.page.get_by_role("navigation")
        expect(header.get_by_text("Log out")).to_be_visible()

    def _create_logout_token(self, overrides=None):
        """Create a CIS2 logout token with optional overrides."""
        now = int(time.time())
        payload = {
            "iss": self.issuer,
            "aud": settings.CIS2_CLIENT_ID,
            "iat": now,
            "exp": now + 300,
            "events": {"http://schemas.openid.net/event/backchannel-logout": {}},
            "sub": self.user_id,  # We currently key on sub to find the local user
            "sid": "not-used",
            "jti": "not-used",
        }

        if overrides:
            # Apply overrides, removing keys with None values
            for key, value in overrides.items():
                if value is None:
                    if key in payload:
                        del payload[key]
                else:
                    payload[key] = value

        headers = {"alg": "RS256", "kid": self.cis2_key_id}
        token = jwt.encode(
            headers, payload, self.cis2_jwk.as_dict(is_private=True)
        )  # Returns bytes
        return token.decode("utf-8")  # Convert to string so we can use in POST later
