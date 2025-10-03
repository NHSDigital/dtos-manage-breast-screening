import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

import pytest
from django.test import TestCase
from test.support.os_helper import EnvironmentVarGuard


@pytest.mark.integration
class TestCallbackEndpoint(TestCase):
    def setUp(self):
        self.env = EnvironmentVarGuard()
        self.env.set("NHS_NOTIFY_APPLICATION_ID", "application_id")
        self.env.set("NHS_NOTIFY_API_KEY", "api_key")

    def test_endpoint_responds_with_json_400(self):
        response = self.client.post(
            "/notifications/message-status/create",
            {},
            enforce_csrf_checks=True,
            content_type="application/json",
        )
        assert response.status_code == 400
        assert response.json() == {
            "error": {
                "message": "Missing API key header",
            },
        }

    def test_endpoint_responds_with_200(self):
        body = {"some": "data"}
        signature = hmac.new(
            bytes("application_id.api_key", "ASCII"),
            msg=bytes(json.dumps(body), "ASCII"),
            digestmod=hashlib.sha256,
        ).hexdigest()
        headers = {
            "X-Api-Key": "api_key",
            "X-HMAC-sha256-signature": signature,
        }

        with patch(
            "manage_breast_screening.notifications.views.Queue.MessageStatusUpdates"
        ) as mock_queue:
            queue_instance = MagicMock()
            mock_queue.return_value = queue_instance

            response = self.client.post(
                "/notifications/message-status/create",
                body,
                enforce_csrf_checks=True,
                content_type="application/json",
                headers=headers,
            )
        assert response.status_code == 200
        assert response.json() == {
            "result": {
                "message": "Message status update queued",
            },
        }
