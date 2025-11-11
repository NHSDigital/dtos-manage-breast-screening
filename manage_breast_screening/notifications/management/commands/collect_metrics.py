import logging
import os

from django.core.management.base import BaseCommand, CommandError

from manage_breast_screening.notifications.services.metrics import Metrics
from manage_breast_screening.notifications.services.queue import Queue

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            for queue in [Queue.RetryMessageBatches(), Queue.MessageStatusUpdates()]:
                metrics = Metrics(
                    queue.queue_name,
                    "messages",
                    "Queue length",
                    os.getenv("ENVIRONMENT"),
                )
                metrics.add("queue_name", queue.get_message_count())
        except Exception as e:
            logger.error(e, exc_info=True)
            raise CommandError(e)
