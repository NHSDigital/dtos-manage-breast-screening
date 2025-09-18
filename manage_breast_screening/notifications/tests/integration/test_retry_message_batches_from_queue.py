import json
import uuid
from unittest.mock import MagicMock, patch

import pytest
import requests

from manage_breast_screening.notifications.management.commands.retry_failed_message_batch import (
    Command,
)
from manage_breast_screening.notifications.models import Message, MessageBatch
from manage_breast_screening.notifications.services.api_client import ApiClient
from manage_breast_screening.notifications.services.queue import Queue
from manage_breast_screening.notifications.tests.factories import (
    MessageBatchFactory,
    MessageFactory,
)
from manage_breast_screening.notifications.tests.integration.helpers import Helpers


@patch("manage_breast_screening.notifications.services.api_client.jwt.encode")
@pytest.mark.integration
class TestRetryMessageBatchesFromQueue:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        monkeypatch.setenv(
            "NHS_NOTIFY_API_MESSAGE_BATCH_URL", "http://localhost:8888/message/batch"
        )
        monkeypatch.setenv("API_OAUTH_TOKEN_URL", "http://localhost:8888/token")
        monkeypatch.setenv("API_OAUTH_API_KEY", "a1b2c3d4")
        monkeypatch.setenv("API_OAUTH_API_KID", "test-1")
        monkeypatch.setenv("API_OAUTH_PRIVATE_KEY", "test-key")

    @pytest.fixture
    def routing_plan_id(self):
        return str(uuid.uuid4())

    @pytest.mark.django_db
    def test_message_batch_is_retried_successfully(
        self, mock_jwt_encode, routing_plan_id, monkeypatch
    ):
        monkeypatch.setenv(
            "QUEUE_STORAGE_CONNECTION_STRING", Helpers().azurite_connection_string()
        )
        message = MessageFactory(status="failed")
        message_batch = MessageBatchFactory(
            routing_plan_id=routing_plan_id, status="failed_recoverable"
        )
        message_batch.messages.set([message])
        message_batch.save()
        queue = Queue.RetryMessageBatches()
        with Helpers().queue_listener(queue, Command().handle):
            queue.add(
                json.dumps(
                    {"message_batch_id": str(message_batch.id), "retry_count": "0"}
                )
            )

        message_batch_actual = MessageBatch.objects.filter(id=message_batch.id)
        assert message_batch_actual[0].status == "sent"
        messages_actual = Message.objects.filter(id=message.id)
        assert messages_actual[0].status == "delivered"

    @patch.object(
        ApiClient, "send_message_batch", return_value=MagicMock(spec=requests.Response)
    )
    @pytest.mark.django_db
    def test_invalid_messages_are_removed(
        self, mock_send_message_batch, mock_jwt_encode, routing_plan_id, monkeypatch
    ):
        monkeypatch.setenv(
            "QUEUE_STORAGE_CONNECTION_STRING", Helpers().azurite_connection_string()
        )
        notify_errors = {
            "errors": [
                {
                    "status": 400,
                    "source": {
                        "pointer": "/data/attributes/messages/1/recipient/nhsNumber"
                    },
                }
            ]
        }

        mock_send_message_batch.return_value.status_code = 400
        mock_send_message_batch.return_value.json.return_value = notify_errors

        invalid_message = MessageFactory(status="failed")
        ok_message_1 = MessageFactory(status="failed")
        ok_message_2 = MessageFactory(status="failed")
        message_batch = MessageBatchFactory(
            routing_plan_id=routing_plan_id,
            status="failed_recoverable",
            messages=[ok_message_1, invalid_message, ok_message_2],
        )
        queue = Queue.RetryMessageBatches()
        with Helpers().queue_listener(queue, Command().handle):
            queue.add(
                json.dumps(
                    {"message_batch_id": str(message_batch.id), "retry_count": "0"}
                )
            )

        invalid_message.refresh_from_db()
        assert invalid_message.status == "failed"
        assert invalid_message.batch is None
        assert invalid_message.nhs_notify_errors == notify_errors["errors"]
