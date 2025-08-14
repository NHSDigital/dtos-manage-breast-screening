import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand, CommandError
from requests import Response

from manage_breast_screening.notifications.management.commands.command_helpers import (
    MessageBatchHelpers,
)
from manage_breast_screening.notifications.models import (
    Appointment,
    Message,
    MessageBatch,
)
from manage_breast_screening.notifications.services.api_client import ApiClient
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


class Command(BaseCommand):
    """
    Django Admin command which finds Appointment records which need batching up to send
    to Communication Management API, and creates MessageBatch and Message records for them.
    """

    def add_arguments(self, parser):
        parser.add_argument("routing_plan_id")

    def handle(self, *args, **options):
        try:
            routing_plan_id = options["routing_plan_id"]

            self.stdout.write("Finding appointments to include in batch...")
            appointments = Appointment.objects.filter(
                starts_at__lte=self.schedule_date(), message__isnull=True, status="B"
            )

            if not appointments:
                self.stdout.write("No appointments found to batch.")
                return

            self.stdout.write(f"Found {appointments.count()} appointments to batch.")

            message_batch = MessageBatch.objects.create(
                routing_plan_id=routing_plan_id,
                scheduled_at=datetime.today().replace(tzinfo=TZ_INFO),
            )

            for appointment in appointments:
                Message.objects.create(appointment=appointment, batch=message_batch)

            self.stdout.write(
                f"Created MessageBatch with ID {message_batch.id} containing {appointments.count()} messages."
            )

            response = ApiClient().send_message_batch(message_batch)

            if response.status_code == 201:
                MessageBatchHelpers.mark_batch_as_sent(message_batch, response.json())
                self.stdout.write(f"{message_batch} sent")
            else:
                self.mark_batch_as_failed(message_batch, response)
                self.stdout.write(
                    f"Failed to send batch. Status: {response.status_code}"
                )
        except Exception as e:
            raise CommandError(e)

    def mark_batch_as_failed(self, message_batch: MessageBatch, response: Response):
        message_batch.notify_errors = response.json()["errors"]
        if response.status_code in RECOVERABLE_STATUS_CODES:
            message_batch.status = "failed_recoverable"
            Queue.RetryMessageBatches().add(
                json.dumps(
                    {
                        "message_batch_id": str(message_batch.id),
                        "retry_count": 0,
                    }
                )
            )
        else:
            message_batch.status = "failed_unrecoverable"
        message_batch.save()

        for message in message_batch.messages.all():
            message.status = "failed"
            message.save()

    # TODO: Check the appointment notification rules here.
    def schedule_date(self) -> datetime:
        today = datetime.today()
        today_end = today.replace(
            hour=23, minute=59, second=59, microsecond=999999, tzinfo=TZ_INFO
        )
        return today_end + timedelta(weeks=4, days=4)
