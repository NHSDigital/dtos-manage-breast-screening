import json
import uuid
from unittest.mock import MagicMock, patch

import pytest

from manage_breast_screening.notifications.management.commands.helpers.message_batch_helpers import (
    MessageBatchHelpers,
)
from manage_breast_screening.notifications.models import (
    Message,
    MessageBatch,
)
from manage_breast_screening.notifications.tests.factories import (
    MessageBatchFactory,
    MessageFactory,
)


class TestMessageBatchHelpers:
    @pytest.fixture
    def routing_plan_id(self):
        return str(uuid.uuid4())

    @pytest.mark.django_db
    def test_mark_messages_as_sent(self):
        message_1 = MessageFactory(status="scheduled")
        message_2 = MessageFactory(status="scheduled")
        message_batch = MessageBatchFactory(status="scheduled")
        message_batch.messages.set([message_1, message_2])
        message_batch.save()

        mock_response_json = {
            "data": {
                "id": "notify_id",
                "attributes": {
                    "messages": [
                        {"messageReference": message_1.id, "id": "id_1"},
                        {"messageReference": message_2.id, "id": "id_2"},
                    ]
                },
            }
        }

        MessageBatchHelpers.mark_batch_as_sent(
            message_batch=message_batch, response_json=mock_response_json
        )

        actual_message_1 = Message.objects.filter(id=message_1.id).first()
        assert actual_message_1 is not None
        assert actual_message_1.notify_id == "id_1"
        assert actual_message_1.status == "delivered"

        actual_message_2 = Message.objects.filter(id=message_2.id).first()
        assert actual_message_2 is not None
        assert actual_message_2.notify_id == "id_2"
        assert actual_message_2.status == "delivered"

        actual_message_batch = MessageBatch.objects.filter(id=message_batch.id).first()
        assert actual_message_batch is not None
        assert actual_message_batch.notify_id == "notify_id"
        assert actual_message_batch.status == "sent"

    @pytest.mark.parametrize("status_code", [401, 403, 404, 405, 406, 413, 415, 422])
    @pytest.mark.django_db
    def test_mark_batch_as_failed_with_unrecoverable_failures(
        self, status_code, routing_plan_id
    ):
        """Test that message batches which fail to send are marked correctly"""
        mock_response = MagicMock()
        mock_response.status_code = status_code
        notify_errors = {"errors": [{"some-error": "details"}]}
        mock_response.json.return_value = notify_errors
        message = MessageFactory(status="scheduled")
        message_batch = MessageBatchFactory(routing_plan_id=routing_plan_id)
        message_batch.messages.set([message])
        message_batch.save()

        MessageBatchHelpers.mark_batch_as_failed(message_batch, mock_response)

        message_batch.refresh_from_db()
        assert message_batch.status == "failed_unrecoverable"
        assert message_batch.nhs_notify_errors == notify_errors
        assert message_batch.messages.count() == 1
        assert message_batch.messages.all()[0].status == "failed"

    @pytest.mark.parametrize("status_code", [400, 408, 425, 429, 500, 503, 504])
    @pytest.mark.django_db
    def test_mark_batch_as_failed_with_recoverable_failures(
        self, status_code, routing_plan_id
    ):
        """Test that message batches which fail to send are marked correctly"""
        mock_response = MagicMock()
        mock_response.status_code = status_code
        notify_errors = {"errors": [{"some-error": "details"}]}
        mock_response.json.return_value = notify_errors
        message_batch = MessageBatchFactory(routing_plan_id=routing_plan_id)

        with patch(
            "manage_breast_screening.notifications.views.Queue.RetryMessageBatches"
        ) as mock_queue:
            queue_instance = MagicMock()
            mock_queue.return_value = queue_instance

            MessageBatchHelpers.mark_batch_as_failed(
                message_batch, mock_response, retry_count=1
            )

            message_batch.refresh_from_db()
            assert message_batch.status == "failed_recoverable"
            assert message_batch.nhs_notify_errors == notify_errors
            queue_instance.add.assert_called_once_with(
                json.dumps(
                    {"message_batch_id": str(message_batch.id), "retry_count": 1}
                )
            )
