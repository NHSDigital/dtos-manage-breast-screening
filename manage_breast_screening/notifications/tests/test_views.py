import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

import pytest
from django.http import JsonResponse
from django.test import RequestFactory

from manage_breast_screening.notifications.views import create_message_status


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    monkeypatch.setenv("APPLICATION_ID", "application_id")
    monkeypatch.setenv("NOTIFY_API_KEY", "api_key")


def test_create_message_status_with_valid_request():
    with patch(
        "manage_breast_screening.notifications.views.Queue.MessageStatusUpdates"
    ) as mock_queue:
        queue_instance = MagicMock()
        mock_queue.return_value = queue_instance

        body = {"some": "data"}

        signature = hmac.new(
            bytes("application_id.api_key", "ASCII"),
            msg=bytes(json.dumps(body), "ASCII"),
            digestmod=hashlib.sha256,
        ).hexdigest()

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Api-Key": "api_key",
            "X-HMAC-sha256-signature": signature,
        }

        req = RequestFactory().post(
            "/notifications/message-status/create",
            body,
            content_type="application/json",
            headers=headers,
        )
        response = create_message_status(req)
        expected_response = JsonResponse(
            {"result": {"message": "Message status update queued"}}, status=200
        )

        assert response.status_code == expected_response.status_code
        assert response.text == expected_response.text
        queue_instance.add.assert_called_once_with(json.dumps(body))


def test_create_message_status_with_invalid_request():
    req = RequestFactory().post(
        "/notifications/message-status/create",
        {"some": "data"},
        content_type="application/json",
        headers={"x-api-key": "api_key", "x-hmac-sha256-signature": "bogus"},
    )
    response = create_message_status(req)
    expected_response = JsonResponse(
        {"error": {"message": "Signature does not match"}}, status=400
    )

    assert response.status_code == expected_response.status_code
    assert response.text == expected_response.text
