import logging
from unittest.mock import Mock

import pytest
from django.test import override_settings

from ..oauth import (
    CustomPrivateKeyJWT,
    _log_response,
    cis2_redirect_uri,
    get_cis2_client,
    jwk_from_public_key,
    oauth,
)


class TestGetCIS2Client:
    def setup_method(self):
        # Clear any cached client between tests
        oauth._clients.pop("cis2", None)

    def teardown_method(self):
        oauth._clients.pop("cis2", None)

    @override_settings(CIS2_CLIENT_ID=None)
    def test_raises_when_client_id_missing(self):
        with pytest.raises(ValueError, match="CIS2_CLIENT_ID"):
            get_cis2_client()

    @override_settings(CIS2_CLIENT_PRIVATE_KEY=None)
    def test_raises_when_private_key_missing(self):
        with pytest.raises(ValueError, match="CIS2_CLIENT_PRIVATE_KEY"):
            get_cis2_client()

    @override_settings(CIS2_CLIENT_PUBLIC_KEY=None)
    def test_raises_when_public_key_missing(self):
        with pytest.raises(ValueError, match="CIS2_CLIENT_PUBLIC_KEY"):
            get_cis2_client()

    @override_settings(CIS2_SERVER_METADATA_URL=None)
    def test_raises_when_metadata_url_missing(self):
        with pytest.raises(ValueError, match="CIS2_SERVER_METADATA_URL"):
            get_cis2_client()

    @override_settings(
        CIS2_CLIENT_ID=None,
        CIS2_CLIENT_PRIVATE_KEY=None,
    )
    def test_lists_all_missing_settings(self):
        with pytest.raises(ValueError, match="CIS2_CLIENT_ID.*CIS2_CLIENT_PRIVATE_KEY"):
            get_cis2_client()

    def test_returns_cached_client_on_second_call(self):
        sentinel = Mock()
        oauth._clients["cis2"] = sentinel

        result = get_cis2_client()

        assert result is sentinel

    def test_registers_and_returns_client(self):
        client = get_cis2_client()

        assert client is not None
        assert "cis2" in oauth._clients


class TestCIS2RedirectUri:
    @override_settings(BASE_URL="https://example.com")
    def test_constructs_redirect_uri(self):
        uri = cis2_redirect_uri()

        assert uri == "https://example.com/auth/cis2/callback"

    @override_settings(BASE_URL="https://example.com/")
    def test_strips_trailing_slash_from_base_url(self):
        uri = cis2_redirect_uri()

        assert uri == "https://example.com/auth/cis2/callback"


class TestJwkFromPublicKey:
    def test_returns_jwk_from_configured_public_key(self):
        jwk = jwk_from_public_key()

        assert jwk is not None
        assert jwk.as_dict()["kty"] == "RSA"

    def test_jwk_has_thumbprint(self):
        jwk = jwk_from_public_key()

        thumbprint = jwk.thumbprint()
        assert isinstance(thumbprint, str)
        assert len(thumbprint) > 0


class TestCustomPrivateKeyJWT:
    def test_default_values(self):
        instance = CustomPrivateKeyJWT(headers={"kid": "test"})

        assert instance.alg == "RS512"
        assert instance.expires_in == 300

    def test_custom_values(self):
        instance = CustomPrivateKeyJWT(
            headers={"kid": "test"}, alg="RS256", expires_in=600
        )

        assert instance.alg == "RS256"
        assert instance.expires_in == 600

    def test_sign_calls_private_key_jwt_sign(self, monkeypatch):
        mock_sign = Mock(return_value="signed-jwt")
        monkeypatch.setattr(
            "manage_breast_screening.auth.oauth.private_key_jwt_sign",
            mock_sign,
        )
        instance = CustomPrivateKeyJWT(headers={"kid": "test-kid"}, expires_in=600)
        auth = Mock(client_secret="secret", client_id="client-id")

        result = instance.sign(auth, "https://token.example.com")

        assert result == "signed-jwt"
        mock_sign.assert_called_once_with(
            "secret",
            client_id="client-id",
            token_endpoint="https://token.example.com",
            header={"kid": "test-kid"},
            alg="RS512",
            expires_in=600,
        )


class TestLogResponse:
    @override_settings(CIS2_DEBUG=False)
    def test_returns_early_when_debug_disabled(self):
        resp = Mock()
        # Should not access resp.request if debug is off
        resp.request = None

        _log_response(resp)

    @override_settings(CIS2_DEBUG=True)
    def test_logs_request_and_response_when_debug_enabled(self, caplog):
        request = Mock()
        request.method = "POST"
        request.url = "https://cis2.example.com/token"
        request.headers = {"Content-Type": "application/x-www-form-urlencoded"}
        request.body = b"grant_type=authorization_code&code=abc"

        resp = Mock()
        resp.request = request
        resp.status_code = 200
        resp.headers = {"Content-Type": "application/json"}
        resp.text = '{"access_token": "xyz"}'

        with caplog.at_level(logging.DEBUG, logger="authlib"):
            _log_response(resp)

        assert "POST https://cis2.example.com/token" in caplog.text
        assert "grant_type" in caplog.text
