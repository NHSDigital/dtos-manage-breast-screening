import datetime
import json
import time

import pytest

from manage_breast_screening.notifications.management.commands.save_message_status import (
    Command,
)
from manage_breast_screening.notifications.models import MessageStatus
from manage_breast_screening.notifications.services.queue import Queue
from manage_breast_screening.notifications.tests.factories import MessageFactory
from manage_breast_screening.notifications.tests.integration.helpers import Helpers


class TestStatusUpdatesFromQueue:
    @pytest.mark.django_db
    def test_message_status_update_is_saved(self, monkeypatch):
        monkeypatch.setenv(
            "QUEUE_STORAGE_CONNECTION_STRING", Helpers().azurite_connection_string()
        )
        message = MessageFactory.create()
        queue = Queue.MessageStatusUpdates()
        with Helpers().queue_listener(queue, Command().handle):
            queue.add(
                json.dumps(
                    {
                        "data": [
                            {
                                "type": "MessageStatus",
                                "attributes": {
                                    "messageReference": str(message.id),
                                    "messageStatus": "delivered",
                                    "messageStatusDescription": "Delivered",
                                    "timestamp": "2025-07-17T14:27:51.413Z",
                                },
                                "meta": {
                                    "idempotencyKey": str(time.time())
                                },  # gitleaks:allow
                            }
                        ]
                    }
                )
            )

        message_statuses = MessageStatus.objects.filter(message=message)
        assert len(message_statuses) == 1
        assert message_statuses[0].status == "delivered"
        assert message_statuses[0].description == "Delivered"
        assert message_statuses[0].status_updated_at == datetime.datetime(
            2025, 7, 17, 14, 27, 51, 413000, tzinfo=datetime.timezone.utc
        )
