import logging

from django.core.management.base import BaseCommand, CommandError

from manage_breast_screening.notifications.services.metrics import Metrics

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            queues = []

            for queue in queues:
                Metrics().set_gauge_value(
                    f"queue_size_{queue.queue_name}",
                    "messages",
                    "Queue length",
                    queue.get_message_count(),
                )

        except Exception as e:
            logger.error(e, exc_info=True)
            raise CommandError(e)
