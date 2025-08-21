import json
import os
import time
from logging import getLogger

from django.core.management.base import BaseCommand, CommandError

from manage_breast_screening.notifications.management.commands.command_helpers import (
    MessageBatchHelpers,
)
from manage_breast_screening.notifications.models import (
    MessageBatch,
    MessageBatchStatusChoices,
)
from manage_breast_screening.notifications.services.api_client import ApiClient
from manage_breast_screening.notifications.services.queue import Queue

logger = getLogger(__name__)


class Command(BaseCommand):
    """
    Django Admin command which takes an ID of a MessageBatch with
    a failed status and retries sending it to the Communications API.
    """

    def handle(self, *args, **options):
        queue = Queue.RetryMessageBatches()
        queue_message = queue.item()

        if queue_message is None:
            logger.info("No messages on queue")
            return

        message_batch_id = json.loads(queue_message.content)["message_batch_id"]
        message_batch = MessageBatch.objects.filter(
            id=message_batch_id,
            status=MessageBatchStatusChoices.FAILED_RECOVERABLE.value,
        ).first()

        if message_batch is None:
            raise CommandError(
                f"Message Batch with id {message_batch_id} and status of '{MessageBatchStatusChoices.FAILED_RECOVERABLE.value}' not found"
            )

        queue.delete(queue_message)

        retry_count = int(json.loads(queue_message.content)["retry_count"])
        if retry_count < int(os.getenv("RETRY_LIMIT", "5")):
            time.sleep(int(os.getenv("RETRY_DELAY", "0")) * retry_count)

            try:
                response = ApiClient().send_message_batch(message_batch)

                if response.status_code == 201:
                    MessageBatchHelpers.mark_batch_as_sent(
                        message_batch=message_batch, response_json=response.json()
                    )
                else:
                    MessageBatchHelpers.mark_batch_as_failed(
                        message_batch, response, retry_count
                    )

                    raise CommandError(
                        f"Message Batch with id {message_batch_id} not sent: {response.status_code}, {response.reason}"
                    )

            except Exception as e:
                queue.add(
                    json.dumps(
                        {
                            "message_batch_id": str(message_batch.id),
                            "retry_count": retry_count + 1,
                        }
                    )
                )
                raise CommandError(e)
        else:
            message_batch.status = MessageBatchStatusChoices.FAILED_UNRECOVERABLE.value
            message_batch.save()
            raise CommandError(
                f"Message Batch with id {message_batch_id} not sent: Retry limit exceeded"
            )
