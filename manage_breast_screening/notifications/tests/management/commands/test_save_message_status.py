import datetime
import json
import time
import uuid
from unittest.mock import MagicMock, patch

import pytest
from azure.storage.queue import QueueMessage
from django.core.management.base import CommandError

from manage_breast_screening.notifications.management.commands.save_message_status import (
    Command,
)
from manage_breast_screening.notifications.models import ChannelStatus, MessageStatus
from manage_breast_screening.notifications.tests.factories import (
    ChannelStatusFactory,
    MessageFactory,
)


@patch(
    "manage_breast_screening.notifications.management.commands.save_message_status.Queue.MessageStatusUpdates"
)
class TestSaveMessageStatus:
    @pytest.mark.django_db
    def test_message_status_is_saved(self, mock_queue):
        message = MessageFactory.create()
        payload = json.dumps(
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
                        "meta": {"idempotencyKey": str(time.time())},  # gitleaks:allow
                    }
                ]
            }
        )
        queue_message = QueueMessage(payload)

        mock_queue.return_value.items.return_value = [queue_message]
        mock_queue.return_value.delete = MagicMock()
        Command().handle()

        status_updates = MessageStatus.objects.filter(message=message)

        assert len(status_updates) == 1
        assert status_updates[0].status == "delivered"
        assert status_updates[0].description == "Delivered"
        assert status_updates[0].status_updated_at == datetime.datetime(
            2025, 7, 17, 14, 27, 51, 413000, tzinfo=datetime.timezone.utc
        )
        mock_queue.return_value.delete.assert_called_once_with(queue_message)

    @pytest.mark.django_db
    def test_channel_status_is_saved(self, mock_queue):
        message = MessageFactory.create()
        mock_queue.return_value.items.return_value = [
            QueueMessage(
                json.dumps(
                    {
                        "data": [
                            {
                                "type": "ChannelStatus",
                                "attributes": {
                                    "messageReference": str(message.id),
                                    "channel": "nhsapp",
                                    "channelStatusDescription": "Read",
                                    "supplierStatus": "read",
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
        ]
        Command().handle()

        status_updates = ChannelStatus.objects.filter(message=message)

        assert len(status_updates) == 1
        assert status_updates[0].channel == "nhsapp"
        assert status_updates[0].description == "Read"
        assert status_updates[0].status == "read"
        assert status_updates[0].status_updated_at == datetime.datetime(
            2025, 7, 17, 14, 27, 51, 413000, tzinfo=datetime.timezone.utc
        )

    @pytest.mark.django_db
    def test_idempotency_key(self, mock_queue):
        message = MessageFactory.create()
        ChannelStatusFactory.create(idempotency_key="not-idempotent", message=message)
        mock_queue.return_value.items.return_value = [
            QueueMessage(
                json.dumps(
                    {
                        "data": [
                            {
                                "type": "ChannelStatus",
                                "attributes": {
                                    "messageReference": str(message.id),
                                    "channel": "sms",
                                    "channelStatusDescription": "Failed",
                                    "supplierStatus": "failed",
                                    "timestamp": "2021-01-01T12:00:00.000Z",
                                },
                                "meta": {
                                    "idempotencyKey": "not-idempotent"
                                },  # gitleaks:allow
                            }
                        ]
                    }
                )
            )
        ]
        Command().handle()

        status_updates = ChannelStatus.objects.filter(message=message)

        assert len(status_updates) == 1

    @pytest.mark.django_db
    def test_message_status_with_no_message_errors(
        self, mock_queue, mock_insights_logger
    ):
        mock_queue.return_value.items.return_value = [
            QueueMessage(
                json.dumps(
                    {
                        "data": [
                            {
                                "type": "ChannelStatus",
                                "attributes": {
                                    "messageReference": str(uuid.uuid4()),
                                    "channel": "sms",
                                    "channelStatusDescription": "Failed",
                                    "supplierStatus": "failed",
                                    "timestamp": "2021-01-01T12:00:00.000Z",
                                },
                                "meta": {
                                    "idempotencyKey": str(time.time())
                                },  # gitleaks:allow
                            }
                        ]
                    }
                )
            )
        ]
        with pytest.raises(CommandError) as err_info:
            Command().handle()

        assert "Message matching query does not exist" in str(err_info.value)

    def test_save_message_status_command_errors(self, mock_queue, mock_insights_logger):
        mock_queue.return_value.items.side_effect = KeyError(
            "QUEUE_STORAGE_CONNECTION_STRING"
        )

        with pytest.raises(CommandError) as err_info:
            Command().handle()

        assert "QUEUE_STORAGE_CONNECTION_STRING" in str(err_info.value)

    @pytest.mark.django_db
    def test_invalid_message_status_is_not_saved(self, mock_queue):
        message = MessageFactory.create()
        mock_queue.return_value.items.return_value = [
            QueueMessage(
                json.dumps(
                    {
                        "data": [
                            {
                                "type": "ChannelStatus",
                                "attributes": {
                                    "messageReference": str(message.id),
                                    "channel": "nhsapp",
                                    "channelStatusDescription": "Invalid status",
                                    "supplierStatus": "invalid-status",
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
        ]
        Command().handle()

        assert len(ChannelStatus.objects.filter(message=message)) == 0

    def test_calls_insights_logger_if_exception_raised(
        self, mock_queue, mock_insights_logger
    ):
        mock_queue.return_value.items.side_effect = Exception("this is an error")

        with pytest.raises(CommandError):
            Command().handle()

        mock_insights_logger.assert_called_once_with(
            "SaveMessageStatusError: this is an error"
        )
