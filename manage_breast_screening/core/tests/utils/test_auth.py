import base64

import pytest

from manage_breast_screening.core.utils.auth import parse_basic_auth


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
