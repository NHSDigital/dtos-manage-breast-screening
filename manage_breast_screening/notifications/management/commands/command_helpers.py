import json
from datetime import datetime
from zoneinfo import ZoneInfo

from requests import Response

from manage_breast_screening.notifications.models import (
    Message,
    MessageBatch,
    MessageBatchStatusChoices,
    MessageStatusChoices,
)
from manage_breast_screening.notifications.services.queue import Queue

TZ_INFO = ZoneInfo("Europe/London")
RECOVERABLE_STATUS_CODES = [
    # Validation error
    400,
    # Client side issue
    408,
    # Retried too early
    425,
    # Too many requests
    429,
    # Server error
    500,
    # Service not accepting requests
    503,
    # Issue with backend services
    504,
]


class MessageBatchHelpers:
    @staticmethod
    def mark_batch_as_sent(message_batch: MessageBatch, response_json: dict):
        message_batch.notify_id = response_json["data"]["id"]
        message_batch.sent_at = datetime.now(tz=TZ_INFO)
        message_batch.status = MessageBatchStatusChoices.SENT.value
        message_batch.save()

        for message_json in response_json["data"]["attributes"]["messages"]:
            message = Message.objects.get(pk=message_json["messageReference"])
            if message:
                message.notify_id = message_json["id"]
                message.status = MessageStatusChoices.DELIVERED.value
                message.save()

    @staticmethod
    def mark_batch_as_failed(
        message_batch: MessageBatch, response: Response, retry_count: int
    ):
        message_batch.nhs_notify_errors = response.json()
        if response.status_code in RECOVERABLE_STATUS_CODES:
            message_batch.status = MessageBatchStatusChoices.FAILED_RECOVERABLE.value
            retry_count = 0 if not retry_count else retry_count + 1
            Queue.RetryMessageBatches().add(
                json.dumps(
                    {
                        "message_batch_id": str(message_batch.id),
                        "retry_count": retry_count,
                    }
                )
            )
        else:
            message_batch.status = MessageBatchStatusChoices.FAILED_UNRECOVERABLE.value
        message_batch.save()

        for message in message_batch.messages.all():
            message.status = MessageStatusChoices.FAILED.value
            message.save()
