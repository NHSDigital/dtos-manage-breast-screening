import json
import os
import time
from logging import getLogger

from django.core.management.base import BaseCommand, CommandError

from manage_breast_screening.notifications.api_client import ApiClient
from manage_breast_screening.notifications.management.commands.command_helpers import (
    MessageBatchHelpers,
)
from manage_breast_screening.notifications.models import MessageBatch
from manage_breast_screening.notifications.services.queue import Queue

logger = getLogger(__name__)


class Command(BaseCommand):
    """
    Django Admin command which takes an ID of a MessageBatch with
    a failed status and retries sending it to the Communications API.
    """

    def handle(self, *args, **options):
        # Look for the MessageBatch and check validity

        queue = Queue.RetryMessageBatches()
        failedMessageBatch = queue.get(1)

        print(failedMessageBatch)

        if failedMessageBatch is None:
            logger.info("No batches in queue")
            return

        queue.delete(failedMessageBatch)

        message_batch = MessageBatch.objects.filter(
            id=failedMessageBatch["message_batch_id"], status="failed_recoverable"
        ).first()
        if message_batch is None:
            raise CommandError(
                f"Message Batch with id {failedMessageBatch['message_batch_id']} and status of 'failed' not found"
            )

        # Try to send the MessageBatch
        if failedMessageBatch["retry_count"] < int(os.getenv("RETRY_LIMIT", 0)):
            time.sleep(os.getenv("RETRY_DELAY") * failedMessageBatch["retry_count"])

            try:
                response = ApiClient().send_message_batch(message_batch)
                if response.status_code == 201:
                    MessageBatchHelpers.mark_batch_as_sent(
                        message_batch=message_batch, response_json=response.json()
                    )
                    raise CommandError(
                        f"Message Batch with id {failedMessageBatch['message_batch_id']} not sent: {response.status_code}, {response.reason}"
                    )

            except Exception as e:
                raise CommandError(e)
                queue.add(
                    json.dumps(
                        {
                            "message_batch_id": str(message_batch.id),
                            "retry_count": failedMessageBatch["retry_count"] + 1,
                        }
                    )
                )
