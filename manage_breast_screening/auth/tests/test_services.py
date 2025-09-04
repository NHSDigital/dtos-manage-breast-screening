import time

import pytest
from authlib.jose import JsonWebKey, jwt
from authlib.jose.errors import (
    ExpiredTokenError,
    InvalidClaimError,
    JoseError,
    MissingClaimError,
)

from manage_breast_screening.auth.services import (
    DecodeLogoutToken,
    InvalidLogoutToken,
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
        client_id: str,
        overrides: dict | None = None,
    ) -> str:
        now = int(time.time())
        payload = {
            "iss": issuer,
            "aud": client_id,
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
        def loader(headers, payload):
            return public_jwk

        return loader

    def test_valid_token_returns_claims(self):
        kid = "k1"
        issuer = "test-issuer"
        client_id = "client-1"
        private_jwk, public_jwk = self._make_keys(kid)
        token = self._make_token(private_jwk, kid, issuer, client_id)

        service = DecodeLogoutToken()
        claims = service.call(
            metadata={"issuer": issuer},
            logout_token=token,
            client_id=client_id,
            key_loader=self._key_loader(public_jwk),
        )

        assert claims["iss"] == issuer
        assert claims["aud"] == client_id
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
        issuer = "test-issuer"
        client_id = "client-1"
        private_jwk, public_jwk = self._make_keys(kid)
        token = self._make_token(
            private_jwk, kid, issuer, client_id, overrides=overrides
        )

        service = DecodeLogoutToken()
        with pytest.raises(InvalidLogoutToken) as excinfo:
            service.call(
                metadata={"issuer": issuer},
                logout_token=token,
                client_id=client_id,
                key_loader=self._key_loader(public_jwk),
            )

        assert isinstance(excinfo.value.__cause__, expected_error_type)
        assert expected_error_text in str(excinfo.value.__cause__)

    def test_invalid_signature_raises_error(self):
        kid = "k1"
        issuer = "test-issuer"
        client_id = "client-1"
        # Create two different key pairs
        private_jwk_1, public_jwk_1 = self._make_keys(kid)
        private_jwk_2, _public_jwk_2 = self._make_keys(kid)
        # Sign with private_jwk_2 but verify with public_jwk_1 -> invalid signature
        token = self._make_token(private_jwk_2, kid, issuer, client_id)

        service = DecodeLogoutToken()
        with pytest.raises(InvalidLogoutToken) as excinfo:
            service.call(
                metadata={"issuer": issuer},
                logout_token=token,
                client_id=client_id,
                key_loader=self._key_loader(public_jwk_1),
            )

        assert isinstance(excinfo.value.__cause__, JoseError)
        assert "signature" in str(excinfo.value.__cause__)

    def test_expired_token_raises_error(self):
        kid = "k1"
        issuer = "test-issuer"
        client_id = "client-1"
        private_jwk, public_jwk = self._make_keys(kid)
        now = int(time.time())
        token = self._make_token(
            private_jwk,
            kid,
            issuer,
            client_id,
            overrides={"exp": now - 120},  # already expired beyond leeway
        )

        service = DecodeLogoutToken()
        with pytest.raises(InvalidLogoutToken) as excinfo:
            service.call(
                metadata={"issuer": issuer},
                logout_token=token,
                client_id=client_id,
                key_loader=self._key_loader(public_jwk),
            )
        assert isinstance(excinfo.value.__cause__, ExpiredTokenError)
        assert "expired" in str(excinfo.value.__cause__)

    def test_missing_iat_raises_error(self):
        kid = "k1"
        issuer = "test-issuer"
        client_id = "client-1"
        private_jwk, public_jwk = self._make_keys(kid)
        # Use overrides to remove the iat claim
        token = self._make_token(
            private_jwk, kid, issuer, client_id, overrides={"iat": None}
        )

        service = DecodeLogoutToken()
        with pytest.raises(InvalidLogoutToken) as excinfo:
            service.call(
                metadata={"issuer": issuer},
                logout_token=token,
                client_id=client_id,
                key_loader=self._key_loader(public_jwk),
            )

        assert isinstance(excinfo.value.__cause__, MissingClaimError)
        assert "iat" in str(excinfo.value.__cause__)
