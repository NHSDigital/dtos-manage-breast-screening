import time

import pytest
from authlib.jose import JsonWebKey, jwt
from authlib.jose.errors import (
    ExpiredTokenError,
    InvalidClaimError,
    JoseError,
    MissingClaimError,
)
from django.conf import settings

from manage_breast_screening.auth.services import (
    InvalidLogoutToken,
    decode_logout_token,
)


class TestDecodeLogoutToken:
    @staticmethod
    def _make_keys(kid: str):
        private_jwk = JsonWebKey.generate_key(
            "RSA", 2048, is_private=True, options={"kid": kid}
        )
        public_jwk = private_jwk.as_dict(is_private=False)
        private_jwk_dict = private_jwk.as_dict(is_private=True)
        return private_jwk_dict, public_jwk

    @staticmethod
    def _make_token(
        private_jwk: dict,
        kid: str,
        issuer: str,
        overrides: dict | None = None,
    ) -> str:
        now = int(time.time())
        payload = {
            "iss": issuer,
            "aud": settings.CIS2_CLIENT_ID,
            "iat": now,
            "exp": now + 300,
            "events": {"http://schemas.openid.net/event/backchannel-logout": {}},
            "sub": "user-123",
        }
        if overrides:
            # Apply overrides, removing keys with None values
            for key, value in overrides.items():
                if value is None:
                    if key in payload:
                        del payload[key]
                else:
                    payload[key] = value

        headers = {"alg": "RS256", "kid": kid}
        token = jwt.encode(headers, payload, private_jwk)
        return token.decode("utf-8")

    @staticmethod
    def _key_loader(public_jwk: dict):
        def loader(_headers, _payload):
            return public_jwk

        return loader

    def test_valid_token_returns_claims(self):
        kid = "k1"
        private_jwk, public_jwk = self._make_keys(kid)
        token = self._make_token(private_jwk, kid, "test-issuer")

        claims = decode_logout_token(
            "test-issuer",
            self._key_loader(public_jwk),
            token,
        )

        assert claims["iss"] == "test-issuer"
        assert claims["aud"] == settings.CIS2_CLIENT_ID
        assert claims["sub"] == "user-123"
        assert "http://schemas.openid.net/event/backchannel-logout" in claims["events"]

    @pytest.mark.parametrize(
        "overrides,expected_error_type,expected_error_text",
        [
            ({"iss": "wrong-issuer"}, InvalidClaimError, "iss"),  # invalid issuer
            ({"aud": "wrong-aud"}, InvalidClaimError, "aud"),  # invalid audience
            (
                {"events": {}},
                InvalidClaimError,
                "events",
            ),  # missing backchannel-logout event
            (
                {"events": {"some-other": {}}},
                InvalidClaimError,
                "events",
            ),  # wrong events
            (
                {"nonce": "should-be-none"},
                InvalidClaimError,
                "nonce",
            ),  # nonce must be None
        ],
    )
    def test_invalid_claims_raise_error(
        self, overrides, expected_error_type, expected_error_text
    ):
        kid = "k1"
        private_jwk, public_jwk = self._make_keys(kid)
        token = self._make_token(private_jwk, kid, "test-issuer", overrides=overrides)

        with pytest.raises(InvalidLogoutToken) as excinfo:
            decode_logout_token(
                "test-issuer",
                self._key_loader(public_jwk),
                token,
            )

        assert isinstance(excinfo.value.__cause__, expected_error_type)
        assert expected_error_text in str(excinfo.value.__cause__)

    def test_invalid_signature_raises_error(self):
        kid = "k1"
        # Create two different key pairs
        private_jwk_1, public_jwk_1 = self._make_keys(kid)
        private_jwk_2, _public_jwk_2 = self._make_keys(kid)
        # Sign with private_jwk_2 but verify with public_jwk_1 -> invalid signature
        token = self._make_token(private_jwk_2, kid, "test-issuer")

        with pytest.raises(InvalidLogoutToken) as excinfo:
            decode_logout_token(
                "test-issuer",
                self._key_loader(public_jwk_1),
                token,
            )

        assert isinstance(excinfo.value.__cause__, JoseError)
        assert "signature" in str(excinfo.value.__cause__)

    def test_expired_token_raises_error(self):
        kid = "k1"
        private_jwk, public_jwk = self._make_keys(kid)
        now = int(time.time())
        token = self._make_token(
            private_jwk,
            kid,
            "test-issuer",
            overrides={"exp": now - 120},  # already expired beyond leeway
        )

        with pytest.raises(InvalidLogoutToken) as excinfo:
            decode_logout_token(
                "test-issuer",
                self._key_loader(public_jwk),
                token,
            )
        assert isinstance(excinfo.value.__cause__, ExpiredTokenError)
        assert "expired" in str(excinfo.value.__cause__)

    def test_missing_iat_raises_error(self):
        kid = "k1"
        private_jwk, public_jwk = self._make_keys(kid)
        # Use overrides to remove the iat claim
        token = self._make_token(
            private_jwk, kid, "test-issuer", overrides={"iat": None}
        )

        with pytest.raises(InvalidLogoutToken) as excinfo:
            decode_logout_token(
                "test-issuer",
                self._key_loader(public_jwk),
                token,
            )

        assert isinstance(excinfo.value.__cause__, MissingClaimError)
        assert "iat" in str(excinfo.value.__cause__)
