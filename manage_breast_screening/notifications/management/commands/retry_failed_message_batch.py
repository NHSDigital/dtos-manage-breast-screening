import json
import os
from logging import getLogger

from django.core.management.base import BaseCommand, CommandError

from manage_breast_screening.notifications.management.commands.helpers.message_batch_helpers import (
    MessageBatchHelpers,
)
from manage_breast_screening.notifications.models import (
    MessageBatch,
    MessageBatchStatusChoices,
)
from manage_breast_screening.notifications.services.api_client import ApiClient
from manage_breast_screening.notifications.services.application_insights_logging import (
    ApplicationInsightsLogging,
)
from manage_breast_screening.notifications.services.queue import Queue

logger = getLogger(__name__)
INSIGHTS_ERROR_NAME = "RetryFailedMessageBatchError"


class Command(BaseCommand):
    """
    Django Admin command which takes an ID of a MessageBatch with
    a failed status and retries sending it to the Communications API.
    """

    def handle(self, *args, **options):
        try:
            self.retry_failed_message_batch()
        except Exception as e:
            ApplicationInsightsLogging().exception(f"{INSIGHTS_ERROR_NAME}: {e}")
            raise CommandError(e)

    def retry_failed_message_batch(self):
        logger.info("Retry Failed Message Batch Command started")
        queue = Queue.RetryMessageBatches()
        logger.debug("Retry queue items: %s", queue.peek())
        queue_message = queue.item()

        if queue_message is None:
            logger.info("No messages on queue")
            return

        message_batch_id = json.loads(queue_message.content)["message_batch_id"]
        message_batch = MessageBatch.objects.filter(
            id=message_batch_id,
            status=MessageBatchStatusChoices.FAILED_RECOVERABLE.value,
        ).first()

        queue.delete(queue_message)
        logger.info(
            "Queue message %s for MessageBatch with id %s deleted from queue",
            queue_message.id,
            message_batch_id,
        )

        if message_batch is None:
            raise CommandError(
                (
                    f"Message Batch with id {message_batch_id} and status of "
                    f"'{MessageBatchStatusChoices.FAILED_RECOVERABLE.value}' not found"
                )
            )

        retry_count = int(json.loads(queue_message.content)["retry_count"])
        if retry_count < int(os.getenv("NOTIFICATIONS_BATCH_RETRY_LIMIT", "5")):
            logger.info(
                "Retrying Message Batch with id %s with retry count %s",
                message_batch_id,
                retry_count,
            )

            response = ApiClient().send_message_batch(message_batch)

            if response.status_code == 201:
                MessageBatchHelpers.mark_batch_as_sent(
                    message_batch=message_batch, response_json=response.json()
                )
            else:
                MessageBatchHelpers.mark_batch_as_failed(
                    message_batch=message_batch,
                    response=response,
                    retry_count=(retry_count + 1),
                )
        else:
            logger.error(
                "Failed Message Batch with id %s not sent: Retry limit exceeded",
                message_batch_id,
            )
            message_batch.status = MessageBatchStatusChoices.FAILED_UNRECOVERABLE.value
            message_batch.save()
            raise CommandError(
                f"Message Batch with id {message_batch_id} not sent: Retry limit exceeded"
            )
