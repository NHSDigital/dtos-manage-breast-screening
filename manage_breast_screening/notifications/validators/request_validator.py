import hashlib
import hmac
import os


class RequestValidator:
    ENCODING = "ASCII"
    API_KEY_HEADER_NAME = "x-api-key"
    SIGNATURE_HEADER_NAME = "x-hmac-sha256-signature"

    def __init__(self, request):
        self.headers = {k.lower(): v for k, v in request.headers.items()}
        self.body = str(request.body.decode(self.ENCODING))

    def valid(self) -> tuple[bool, str]:
        is_valid, error_message = self.verify_headers()
        if not is_valid:
            return False, error_message

        if not self.verify_signature():
            return False, "Signature does not match"

        return True, ""

    def verify_headers(self) -> tuple[bool, str]:
        if self.headers.get(self.API_KEY_HEADER_NAME) is None:
            return False, "Missing API key header"

        if self.headers.get(self.API_KEY_HEADER_NAME) != os.getenv("NOTIFY_API_KEY"):
            return False, "Invalid API key"

        if self.headers.get(self.SIGNATURE_HEADER_NAME) is None:
            return False, "Missing signature header"

        return True, ""

    def verify_signature(self) -> bool:
        secret = f"{os.getenv('APPLICATION_ID')}.{os.getenv('NOTIFY_API_KEY')}"
        expected_signature = hmac.new(
            bytes(secret, self.ENCODING),
            msg=bytes(self.body, self.ENCODING),
            digestmod=hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(
            expected_signature,
            self.headers[self.SIGNATURE_HEADER_NAME],
        )
