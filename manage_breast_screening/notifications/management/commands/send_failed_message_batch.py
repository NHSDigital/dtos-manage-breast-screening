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
        # get the batch from the queue in an iterator

        queue = Queue.RetryMessageBatches()
        failed_message_batch_iterator = queue.items(1)

        # return if there isn't a message_batch
        try:
            failed_queue_message = failed_message_batch_iterator.next()
        except StopIteration as e:
            logger.info(e)
            return

        message_batch_id = json.loads(failed_queue_message.content)["message_batch_id"]
        message_batch = MessageBatch.objects.filter(
            id=message_batch_id, status="failed_recoverable"
        ).first()

        if message_batch is None:
            raise CommandError(
                f"Message Batch with id {message_batch_id} and status of 'failed_recoverable' not found"
            )

        # Try to send the MessageBatch
        retry_count = int(json.loads(failed_queue_message.content)["retry_count"])
        if retry_count < int(os.getenv("RETRY_LIMIT", "5")):
            time.sleep(int(os.getenv("RETRY_DELAY", "0")) * retry_count)

            try:
                queue.delete(failed_queue_message)

                response = ApiClient().send_message_batch(message_batch)

                if response.status_code == 201:
                    MessageBatchHelpers.mark_batch_as_sent(
                        message_batch=message_batch, response_json=response.json()
                    )
                else:
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
