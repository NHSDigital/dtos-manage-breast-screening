import json

from dateutil import parser
from django.core.management.base import BaseCommand, CommandError

from manage_breast_screening.notifications.models import (
    ChannelStatus,
    Message,
    MessageStatus,
)
from manage_breast_screening.notifications.services.queue import Queue


class Command(BaseCommand):
    """
    Django Admin command which reads message status updates from an Azure Storage Queue
    and creates MessageStatus and ChannelStatus records in the database.
    """

    def handle(self, *args, **options):
        try:
            queue = Queue.MessageStatusUpdates()
            for item in queue.items():
                payload = json.loads(item.content)
                self.data = payload["data"][0]
                message_id = self.data["attributes"]["messageReference"]
                self.message = Message.objects.get(pk=message_id)
                self.idempotency_key = self.data["meta"]["idempotencyKey"]

                if self.save_status_update():
                    queue.delete(item)
        except Exception as e:
            raise CommandError(e)

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

        MessageStatus(
            message=self.message,
            description=self.data["attributes"]["messageStatusDescription"],
            idempotency_key=self.idempotency_key,
            status=self.data["attributes"]["messageStatus"],
            status_updated_at=parser.parse(self.data["attributes"]["timestamp"]),
        ).save()

    def save_channel_status(self):
        if ChannelStatus.objects.filter(idempotency_key=self.idempotency_key).exists():
            return

        ChannelStatus(
            message=self.message,
            channel=self.data["attributes"]["channel"],
            description=self.data["attributes"]["channelStatusDescription"],
            idempotency_key=self.idempotency_key,
            status=self.data["attributes"]["supplierStatus"],
            status_updated_at=parser.parse(self.data["attributes"]["timestamp"]),
        ).save()
