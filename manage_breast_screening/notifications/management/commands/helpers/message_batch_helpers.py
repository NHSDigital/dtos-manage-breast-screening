import json
import re
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
VALIDATION_ERROR_STATUS_CODE = 400
MESSAGE_PATH_REGEX = r"(?<=\/data\/attributes\/messages\/)(\d*)(?=\/)"


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
        message_batch: MessageBatch, response: Response, retry_count: int = 0
    ):
        message_batch.nhs_notify_errors = response.json()
        if response.status_code in RECOVERABLE_STATUS_CODES:
            message_batch.status = MessageBatchStatusChoices.FAILED_RECOVERABLE.value
            Queue.RetryMessageBatches().add(
                json.dumps(
                    {
                        "message_batch_id": str(message_batch.id),
                        "retry_count": retry_count,
                    }
                )
            )
        elif response.status_code == VALIDATION_ERROR_STATUS_CODE:
            MessageBatchHelpers.process_validation_errors(message_batch, retry_count)
        else:
            message_batch.status = MessageBatchStatusChoices.FAILED_UNRECOVERABLE.value
        message_batch.save()

        for message in message_batch.messages.all():
            message.status = MessageStatusChoices.FAILED.value
            message.sent_at = datetime.now(tz=TZ_INFO)
            message.save()

    @staticmethod
    def process_validation_errors(message_batch: MessageBatch, retry_count: int = 0):
        message_batch_errors = json.loads(message_batch.nhs_notify_errors).get("errors")

        messages = list(Message.objects.filter(batch=message_batch).all())
        for error in message_batch_errors:
            message_index_result = re.search(
                MESSAGE_PATH_REGEX, error["source"]["pointer"]
            )
            if message_index_result is not None:
                message_index = int(message_index_result.group(0))
                message = messages[message_index]
                message.batch = None
                if message.nhs_notify_errors is None:
                    message.nhs_notify_errors = json.dumps([error])
                else:
                    message.nhs_notify_errors = json.dumps(
                        json.loads(message.nhs_notify_errors) + [error]
                    )
                message.save()

        message_batch.status = MessageBatchStatusChoices.FAILED_RECOVERABLE.value
        message_batch.save()
        Queue.RetryMessageBatches().add(
            json.dumps(
                {
                    "message_batch_id": str(message_batch.id),
                    "retry_count": retry_count,
                }
            )
        )
