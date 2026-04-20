import json
from unittest.mock import Mock, patch

import jwt
import pytest

from ..token_validator import TokenValidator


@patch(f"{TokenValidator.__module__}.logger")
class TestTokenValidator:
    @pytest.fixture(autouse=True)
    def setup_env(self):
        with patch.dict(
            "os.environ",
            {
                "API_AUDIENCE": "test_audience",
                "TENANT_ID": "test_tenant_id",
                "BYPASS_API_TOKEN_AUTH": "false",
            },
        ):
            yield

    @pytest.fixture
    def mock_urlopen_response(self):
        return {
            "keys": [
                {
                    "kid": "abc123",
                    "kty": "RSA",
                    "use": "sig",
                    "n": "modulus",
                    "e": "exponent",
                }
            ]
        }

    @pytest.fixture
    def mock_urlopen(self, mock_urlopen_response):
        with patch(f"{TokenValidator.__module__}.urlopen") as mock_urlopen:
            mock_urlopen.return_value.read.return_value = json.dumps(
                mock_urlopen_response
            ).encode("utf-8")
            yield mock_urlopen

    @pytest.fixture
    def mock_get_unverified_header(self):
        with patch(
            f"{TokenValidator.__module__}.jwt.get_unverified_header"
        ) as mock_get_unverified_header:
            mock_get_unverified_header.return_value = {"kid": "abc123"}
            yield mock_get_unverified_header

    @patch(f"{TokenValidator.__module__}.urlopen")
    def test_with_no_matching_rsa_key(self, mock_urlopen, mock_logger):
        mock_urlopen.return_value.read.return_value = '{"keys": []}'
        validator = TokenValidator()
        assert validator(Mock(headers={"Authorization": "Bearer abc123"})) is None
        mock_logger.error.assert_called_with("Unable to find appropriate key")

    def test_with_matching_rsa_key(self, _, mock_get_unverified_header, mock_urlopen):
        validator = TokenValidator()
        rsa_key = validator._rsa_key("abc123")
        assert rsa_key == {
            "kty": "RSA",
            "kid": "abc123",
            "use": "sig",
            "n": "modulus",
            "e": "exponent",
        }

    @patch(
        f"{TokenValidator.__module__}.jwt.decode", side_effect=jwt.ExpiredSignatureError
    )
    def test_with_expired_signature(
        self, mock_jwt_decode, mock_logger, mock_get_unverified_header, mock_urlopen
    ):
        validator = TokenValidator()
        assert validator(Mock(headers={"Authorization": "Bearer abc123"})) is None
        mock_logger.exception.assert_called_with("Token is expired")

    @patch(
        f"{TokenValidator.__module__}.jwt.decode", side_effect=jwt.InvalidAudienceError
    )
    def test_with_invalid_claims(
        self, mock_jwt_decode, mock_logger, mock_get_unverified_header, mock_urlopen
    ):
        validator = TokenValidator()
        assert validator(Mock(headers={"Authorization": "Bearer abc123"})) is None
        mock_logger.exception.assert_called_with(
            "Invalid claims. Please check the audience and issuer."
        )

    @patch(
        f"{TokenValidator.__module__}.jwt.decode", side_effect=jwt.InvalidIssuerError
    )
    def test_with_invalid_issuer(
        self, mock_jwt_decode, mock_logger, mock_get_unverified_header, mock_urlopen
    ):
        validator = TokenValidator()
        assert validator(Mock(headers={"Authorization": "Bearer abc123"})) is None
        mock_logger.exception.assert_called_with(
            "Invalid claims. Please check the audience and issuer."
        )

    @patch(f"{TokenValidator.__module__}.jwt.decode", side_effect=jwt.InvalidTokenError)
    def test_with_invalid_token(
        self, mock_jwt_decode, mock_logger, mock_get_unverified_header, mock_urlopen
    ):
        validator = TokenValidator()
        assert validator(Mock(headers={"Authorization": "Bearer abc123"})) is None
        mock_logger.exception.assert_called_with("Token is invalid")

    @patch(f"{TokenValidator.__module__}.jwt.decode", side_effect=Exception)
    def test_with_unexpected_exception(
        self, mock_jwt_decode, mock_logger, mock_get_unverified_header, mock_urlopen
    ):
        validator = TokenValidator()
        assert validator(Mock(headers={"Authorization": "Bearer abc123"})) is None
        mock_logger.exception.assert_called_with(
            "Unable to parse authentication token."
        )

    @patch(
        f"{TokenValidator.__module__}.jwt.decode", return_value={"sub": "1234567890"}
    )
    def test_with_valid_token(
        self, mock_jwt_decode, _, mock_get_unverified_header, mock_urlopen
    ):
        validator = TokenValidator()
        assert validator(Mock(headers={"Authorization": "Bearer abc123"})) == {
            "sub": "1234567890"
        }

    def test_authentication_bypass_enabled(self, mock_logger):
        with patch.dict("os.environ", {"BYPASS_API_TOKEN_AUTH": "true"}):
            validator = TokenValidator()
            assert validator(Mock(headers={"Authorization": "Bearer anytoken"})) == {
                "sub": "bypass_user"
            }
