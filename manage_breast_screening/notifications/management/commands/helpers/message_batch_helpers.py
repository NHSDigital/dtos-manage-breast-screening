import json
import logging
import re
from datetime import datetime

from requests import Response

from manage_breast_screening.notifications.models import (
    ZONE_INFO,
    Message,
    MessageBatch,
    MessageBatchStatusChoices,
    MessageStatusChoices,
)
from manage_breast_screening.notifications.services.application_insights_logging import (
    ApplicationInsightsLogging,
)
from manage_breast_screening.notifications.services.queue import Queue

logger = logging.getLogger(__name__)

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
        message_batch.sent_at = datetime.now(tz=ZONE_INFO)
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
        log_msg = "Marking batch %s as failed. Response code: %s. Response: %s" % (
            message_batch.id,
            response.status_code,
            response.text,
        )
        ApplicationInsightsLogging().custom_event_warning(
            message=log_msg,
            event_name="batch_marked_as_failed",
        )

        try:
            message_batch.nhs_notify_errors = response.json()
        except Exception:
            message_batch.nhs_notify_errors = {"errors": response.text}

        if response.status_code in RECOVERABLE_STATUS_CODES:
            MessageBatchHelpers.process_recoverable_batch(message_batch, retry_count)
        elif response.status_code == VALIDATION_ERROR_STATUS_CODE:
            MessageBatchHelpers.process_validation_errors(message_batch, retry_count)
        else:
            MessageBatchHelpers.process_unrecoverable_batch(message_batch)

    @staticmethod
    def process_validation_errors(message_batch: MessageBatch, retry_count: int = 0):
        message_batch_errors = message_batch.nhs_notify_errors.get("errors")

        messages = list(Message.objects.filter(batch=message_batch).all())
        for error in message_batch_errors:
            message_index_result = re.search(
                MESSAGE_PATH_REGEX, error["source"]["pointer"]
            )
            if message_index_result is not None:
                message_index = int(message_index_result.group(0))
                message = messages[message_index]
                message.batch = None
                message.status = MessageStatusChoices.FAILED.value

                if message.nhs_notify_errors is None:
                    message.nhs_notify_errors = [error]
                else:
                    message.nhs_notify_errors = message.nhs_notify_errors + [error]

                message.save()

        message_batch.status = MessageBatchStatusChoices.FAILED_RECOVERABLE.value
        message_batch.save()

        logger.info(
            "Adding MessageBatch %s to retry queue after validation failure",
            message_batch.id,
        )

        Queue.RetryMessageBatches().add(
            json.dumps(
                {
                    "message_batch_id": str(message_batch.id),
                    "retry_count": retry_count,
                }
            )
        )

    @staticmethod
    def process_unrecoverable_batch(message_batch: MessageBatch):
        message_batch.status = MessageBatchStatusChoices.FAILED_UNRECOVERABLE.value
        message_batch.save()
        for message in message_batch.messages.all():
            message.status = MessageStatusChoices.FAILED.value
            message.sent_at = datetime.now(tz=ZONE_INFO)
            message.save()

        logger.error(
            "MessageBatch %s failed to send. Unrecoverable failure.", message_batch.id
        )

    @staticmethod
    def process_recoverable_batch(message_batch: MessageBatch, retry_count: int):
        message_batch.status = MessageBatchStatusChoices.FAILED_RECOVERABLE.value
        message_batch.save()

        logger.info(
            "Adding MessageBatch %s to retry queue after recoverable failure",
            message_batch.id,
        )

        Queue.RetryMessageBatches().add(
            json.dumps(
                {
                    "message_batch_id": str(message_batch.id),
                    "retry_count": retry_count,
                }
            )
        )
