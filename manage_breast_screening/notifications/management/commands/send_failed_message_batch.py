from django.core.management.base import BaseCommand, CommandError

from manage_breast_screening.notifications.api_client import ApiClient
from manage_breast_screening.notifications.management.commands.command_helpers import (
    MessageBatchHelpers,
)
from manage_breast_screening.notifications.models import MessageBatch


class Command(BaseCommand):
    """
    Django Admin command which takes an ID of a MessageBatch with
    a failed status and retries sending it to the Communications API.
    """

    def add_arguments(self, parser):
        parser.add_argument("message_batch_id")

    def handle(self, *args, **options):
        # Look for the MessageBatch and check validity
        batch_id = options["message_batch_id"]
        message_batch = MessageBatch.objects.filter(
            id=batch_id, status="failed"
        ).first()
        if message_batch is None:
            raise CommandError(
                f"Message Batch with id {batch_id} and status of 'failed' not found"
            )

        # Try to send the MessageBatch
        try:
            response = ApiClient().send_message_batch(message_batch)
            if response.status_code == 201:
                MessageBatchHelpers.mark_batch_as_sent(
                    message_batch=message_batch, response_json=response.json()
                )
            else:
                raise CommandError(
                    f"Message Batch with id {batch_id} not sent: {response.status_code}, {response.reason}"
                )

        except Exception as e:
            raise CommandError(e)
