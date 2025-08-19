import json
import uuid
from unittest.mock import patch

import pytest

from manage_breast_screening.notifications.management.commands.retry_failed_message_batch import (
    Command,
)
from manage_breast_screening.notifications.models import Message, MessageBatch
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
            "API_MESSAGE_BATCH_URL", "http://localhost:8888/message/batch"
        )
        monkeypatch.setenv("OAUTH_TOKEN_URL", "http://localhost:8888/token")
        monkeypatch.setenv("OAUTH_API_KEY", "a1b2c3d4")
        monkeypatch.setenv("OAUTH_API_KID", "test-1")
        monkeypatch.setenv("PRIVATE_KEY", "test-key")
        monkeypatch.setenv("CMAPI_CONSUMER_KEY", "consumer-key")

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
