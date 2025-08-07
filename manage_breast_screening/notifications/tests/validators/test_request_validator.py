import hashlib
import hmac
import json
import os
from unittest.mock import MagicMock

import pytest

from manage_breast_screening.notifications.validators.request_validator import (
    RequestValidator,
)


class TestRequestValidator:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        """Set up environment variables for tests."""
        monkeypatch.setenv("APPLICATION_ID", "application_id")
        monkeypatch.setenv("NOTIFY_API_KEY", "api_key")

    def mock_request(self, headers={}, body="{}"):
        req = MagicMock()
        req.headers = headers
        req.body = bytes(body, "ASCII")
        return req

    def create_digest(self, secret: str, body: str) -> str:
        return hmac.new(
            bytes(secret, "ASCII"), msg=bytes(body, "ASCII"), digestmod=hashlib.sha256
        ).hexdigest()

    def test_verify_signature_invalid(self):
        """Test that an invalid signature fails verification."""
        headers = {RequestValidator.SIGNATURE_HEADER_NAME: "signature"}
        body = json.dumps({"data": [{"body": "valid"}]})

        req = self.mock_request(headers, body)
        assert not RequestValidator(req).verify_signature()

    def test_verify_signature_valid(self):
        """Test that a valid signature passes verification."""
        body = json.dumps({"data": [{"body": "valid"}]})
        signature = self.create_digest("application_id.api_key", body)

        headers = {RequestValidator.SIGNATURE_HEADER_NAME: signature}
        req = self.mock_request(headers, body)
        assert RequestValidator(req).verify_signature()

    def test_valid_missing_all_headers(self):
        """Test that missing all headers fails verification."""
        assert RequestValidator(self.mock_request()).valid() == (
            False,
            "Missing API key header",
        )

    def test_valid_missing_api_key_header(self):
        """Test that missing API key header fails verification."""
        headers = {RequestValidator.SIGNATURE_HEADER_NAME: "signature"}
        req = self.mock_request(headers)
        assert RequestValidator(req).valid() == (False, "Missing API key header")

    def test_valid_missing_signature_header(self):
        """Test that missing signature header fails verification."""
        headers = {RequestValidator.API_KEY_HEADER_NAME: "api_key"}
        req = self.mock_request(headers)
        assert RequestValidator(req).valid() == (False, "Missing signature header")

    def test_valid_with_invalid_api_key(self):
        """Test that an invalid API key fails verification."""
        headers = {RequestValidator.API_KEY_HEADER_NAME: "invalid_api_key"}
        req = self.mock_request(headers)
        assert RequestValidator(req).valid() == (False, "Invalid API key")

    def test_valid(self):
        """Test that valid API key and signature headers pass verification."""
        body = '{"this": "that"}'
        secret = f"{os.getenv('APPLICATION_ID')}.{os.getenv('NOTIFY_API_KEY')}"
        signature = self.create_digest(secret, body)

        headers = {
            RequestValidator.API_KEY_HEADER_NAME: "api_key",
            RequestValidator.SIGNATURE_HEADER_NAME: signature,
        }
        req = self.mock_request(headers, body)
        assert RequestValidator(req).valid() == (True, "")
