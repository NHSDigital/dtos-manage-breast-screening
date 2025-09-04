from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand, CommandError

from manage_breast_screening.notifications.management.commands.helpers.message_batch_helpers import (
    MessageBatchHelpers,
)
from manage_breast_screening.notifications.management.commands.helpers.routing_plan import (
    RoutingPlan,
)
from manage_breast_screening.notifications.models import (
    Appointment,
    Message,
    MessageBatch,
    MessageBatchStatusChoices,
)
from manage_breast_screening.notifications.services.api_client import ApiClient

TZ_INFO = ZoneInfo("Europe/London")


class Command(BaseCommand):
    """
    Django Admin command which finds Appointment records which need batching up to send
    to Communication Management API, and creates MessageBatch and Message records for them.
    """

    def handle(self, *args, **options):
        try:
            for routing_plan in RoutingPlan.all():
                self.stdout.write(
                    f"Finding appointments of episode type {routing_plan.episode_types} to include in batch."
                )

                appointments = Appointment.objects.filter(
                    episode_type__in=routing_plan.episode_types,
                    starts_at__lte=self.schedule_date(),
                    message__isnull=True,
                    status="B",
                )

                if not appointments:
                    self.stdout.write(
                        f"No appointments found to batch for episode types {routing_plan.episode_types}"
                    )
                    continue

                self.stdout.write(
                    f"Found {appointments.count()} appointments to batch."
                )

                message_batch = MessageBatch.objects.create(
                    routing_plan_id=routing_plan.id,
                    scheduled_at=datetime.now(tz=TZ_INFO),
                    status=MessageBatchStatusChoices.SCHEDULED.value,
                )

                for appointment in appointments:
                    Message.objects.create(appointment=appointment, batch=message_batch)

                self.stdout.write(
                    f"Created MessageBatch with ID {message_batch.id} containing {appointments.count()} messages."
                )

                response = ApiClient().send_message_batch(message_batch)

                if response.status_code == 201:
                    MessageBatchHelpers.mark_batch_as_sent(
                        message_batch, response.json()
                    )
                    self.stdout.write(f"{message_batch} sent")
                else:
                    MessageBatchHelpers.mark_batch_as_failed(
                        message_batch, response, retry_count=0
                    )
                    self.stdout.write(
                        f"Failed to send batch. Status: {response.status_code}"
                    )
        except Exception as e:
            raise CommandError(e)

    # TODO: Check the appointment notification rules here.
    def schedule_date(self) -> datetime:
        today = datetime.now(tz=TZ_INFO)
        today_end = today.replace(hour=23, minute=59, second=59, microsecond=999999)
        return today_end + timedelta(weeks=4, days=4)
