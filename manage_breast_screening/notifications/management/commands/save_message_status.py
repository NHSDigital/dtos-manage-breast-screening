import json
from logging import getLogger

from dateutil import parser
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand

from manage_breast_screening.notifications.management.commands.helpers.exception_handler import (
    exception_handler,
)
from manage_breast_screening.notifications.models import (
    ChannelStatus,
    Message,
    MessageStatus,
)
from manage_breast_screening.notifications.services.queue import Queue

INSIGHTS_JOB_NAME = "SaveMessageStatus"
logger = getLogger(__name__)


class Command(BaseCommand):
    """
    Django Admin command which reads message status updates from an Azure Storage Queue
    and creates MessageStatus and ChannelStatus records in the database.
    """

    def handle(self, *args, **options):
        with exception_handler(INSIGHTS_JOB_NAME):
            logger.info("Save Message Status Command started")
            queue = Queue.MessageStatusUpdates()
            for item in queue.items():
                logger.debug(f"Processing message status update {item}")
                payload = json.loads(item.content)
                queue.delete(item)
                self.data = payload["data"][0]
                message_id = self.data["attributes"]["messageReference"]
                self.message = Message.objects.get(pk=message_id)
                self.idempotency_key = self.data["meta"]["idempotencyKey"]

                if self.save_status_update():
                    logger.info(f"Message status update {item} saved")

    def save_status_update(self) -> bool:
        try:
            if self.data["type"] == "ChannelStatus":
                self.save_channel_status()
                return True
            if self.data["type"] == "MessageStatus":
                self.save_message_status()
                return True
        except ValueError:
            pass

        return False

    def save_message_status(self):
        if MessageStatus.objects.filter(idempotency_key=self.idempotency_key).exists():
            return

        status_record = MessageStatus(
            message=self.message,
            description=self.data["attributes"]["messageStatusDescription"],
            idempotency_key=self.idempotency_key,
            status=self.data["attributes"]["messageStatus"],
            status_updated_at=parser.parse(self.data["attributes"]["timestamp"]),
        )
        try:
            status_record.full_clean()
            status_record.save()
        except ValidationError as e:
            logger.error(e, exc_info=True)
            pass

    def save_channel_status(self):
        if ChannelStatus.objects.filter(idempotency_key=self.idempotency_key).exists():
            return

        status_record = ChannelStatus(
            message=self.message,
            channel=self.data["attributes"]["channel"],
            description=self.data["attributes"]["channelStatusDescription"],
            idempotency_key=self.idempotency_key,
            status=self.data["attributes"]["supplierStatus"],
            status_updated_at=parser.parse(self.data["attributes"]["timestamp"]),
        )
        try:
            status_record.full_clean()
            status_record.save()
        except ValidationError as e:
            logger.error(e, exc_info=True)
            pass
