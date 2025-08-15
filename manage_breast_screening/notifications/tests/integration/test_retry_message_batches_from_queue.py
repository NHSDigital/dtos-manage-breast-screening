import json

import pytest

from manage_breast_screening.notifications.management.commands.send_failed_message_batch import (
    Command,
)
from manage_breast_screening.notifications.services.queue import Queue
from manage_breast_screening.notifications.tests.factories import MessageBatchFactory
from manage_breast_screening.notifications.tests.integration.helpers import Helpers


class TestRetryMessageBatchesFromQueue:
    @pytest.mark.django_db
    def test_message_batch_is_retried_successfully(self, monkeypatch):
        monkeypatch.setenv(
            "QUEUE_STORAGE_CONNECTION_STRING", Helpers().azurite_connection_string()
        )
        message_batch = MessageBatchFactory.build()
        queue = Queue.RetryMessageBatches()
        queue.add(
            json.dumps({"message_batch_id": message_batch.id, "retry_count": "0"})
        )

        Command().handle

        # TODO: test the message_batch has been sent successfully and marked as sent
