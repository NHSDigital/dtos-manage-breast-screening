from datetime import datetime, timedelta
from logging import getLogger

from business.calendar import Calendar
from django.core.management.base import BaseCommand

from manage_breast_screening.config.settings import boolean_env
from manage_breast_screening.notifications.management.commands.helpers.command_handler import (
    CommandHandler,
)
from manage_breast_screening.notifications.management.commands.helpers.message_batch_helpers import (
    MessageBatchHelpers,
)
from manage_breast_screening.notifications.management.commands.helpers.routing_plan import (
    RoutingPlan,
)
from manage_breast_screening.notifications.models import (
    ZONE_INFO,
    Appointment,
    Message,
    MessageBatch,
    MessageBatchStatusChoices,
)
from manage_breast_screening.notifications.services.api_client import ApiClient

INSIGHTS_JOB_NAME = "SendMessageBatch"
logger = getLogger(__name__)


class Command(BaseCommand):
    """
    Django Admin command which finds Appointment records which need batching up to send
    to Communication Management API, and creates MessageBatch and Message records for them.
    """

    def handle(self, *args, **options):
        with CommandHandler.handle(INSIGHTS_JOB_NAME):
            return self.send_message_batch()

    def send_message_batch(self):
        logger.info("Send Message Batch Command started")
        if not self.bso_working_day():
            return

        for routing_plan in RoutingPlan.all():
            logger.info(f"Processing Routing Plan {routing_plan.id}")
            self.stdout.write(
                f"Finding appointments of episode type {routing_plan.episode_types} to include in batch."
            )

            appointments = Appointment.objects.filter(
                episode_type__in=routing_plan.episode_types,
                starts_at__lte=self.schedule_date(),
                message__isnull=True,
                status="B",
                number="1",
            )

            if not appointments:
                logger.info(
                    f"No appointments found to batch for episode types {routing_plan.episode_types}"
                )
                continue

            logger.info(f"Found {appointments.count()} appointments to batch.")

            message_batch = MessageBatch.objects.create(
                routing_plan_id=routing_plan.id,
                scheduled_at=datetime.now(tz=ZONE_INFO),
                status=MessageBatchStatusChoices.SCHEDULED.value,
                silent=self.silent_mode(),
            )

            for appointment in appointments:
                Message.objects.create(appointment=appointment, batch=message_batch)

            logger.info(
                f"Created MessageBatch with ID {message_batch.id} containing {appointments.count()} messages."
            )

            if self.silent_mode():
                MessageBatchHelpers.mark_batch_as_silent_sent(message_batch)
            else:
                response = ApiClient().send_message_batch(message_batch)

                if response.status_code == 201:
                    MessageBatchHelpers.mark_batch_as_sent(
                        message_batch, response.json()
                    )
                    logger.info(f"{message_batch} sent successfully")
                else:
                    logger.error(
                        f"Failed to send batch. Status: {response.status_code}"
                    )
                    MessageBatchHelpers.mark_batch_as_failed(
                        message_batch, response, retry_count=0
                    )

    def bso_working_day(self):
        return Calendar().is_business_day(datetime.now(tz=ZONE_INFO))

    def schedule_date(self) -> datetime:
        today = datetime.now(tz=ZONE_INFO)
        today_end = today.replace(hour=23, minute=59, second=59, microsecond=999999)

        return today_end + timedelta(weeks=4)

    def silent_mode(self):
        return boolean_env("NOTIFICATIONS_SILENT_MODE", False)
