import pytest

from manage_breast_screening.notifications.management.commands.command_helpers import (
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


class TestMessageBatchFunctions:
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
        assert (
            actual_message_1.notify_id == "id_1"
            if actual_message_1 is not None
            else False
        )
        assert (
            actual_message_1.status == "delivered"
            if actual_message_1 is not None
            else False
        )

        actual_message_2 = Message.objects.filter(id=message_2.id).first()
        assert (
            actual_message_2.notify_id == "id_2"
            if actual_message_2 is not None
            else False
        )
        assert (
            actual_message_2.status == "delivered"
            if actual_message_2 is not None
            else False
        )

        actual_message_batch = MessageBatch.objects.filter(id=message_batch.id).first()
        assert (
            actual_message_batch.notify_id == "notify_id"
            if actual_message_batch is not None
            else False
        )
        assert (
            actual_message_batch.status == "sent"
            if actual_message_batch is not None
            else False
        )
