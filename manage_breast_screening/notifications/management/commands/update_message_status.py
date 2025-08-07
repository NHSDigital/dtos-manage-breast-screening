import json

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
            for item in Queue.MessageStatusUpdates().items():
                payload = json.loads(item)
                update_type = payload["data"][0]["type"]
                idempotency_key = payload["data"][0]["meta"]["idempotencyKey"]
                attributes = payload["data"][0]["attributes"]
                message = Message.objects.get(pk=attributes["messageReference"])

                if message and update_type == "ChannelStatus":
                    if not ChannelStatus.objects.exists(
                        idempotency_key=idempotency_key
                    ):
                        ChannelStatus(
                            message=message,
                            channel=attributes["channel"],
                            description=attributes["channelStatusDescription"],
                            idempotency_key=idempotency_key,
                            status=attributes["supplierStatus"],
                            status_updated_at=attributes["timestamp"],
                        ).save()

                if message and update_type == "MessageStatus":
                    if not MessageStatus.objects.exists(
                        idempotency_key=idempotency_key
                    ):
                        MessageStatus(
                            message=message,
                            description=attributes["messageStatusDescription"],
                            idempotency_key=idempotency_key,
                            status=attributes["messageStatus"],
                            status_updated_at=attributes["timestamp"],
                        ).save()

        except Exception as e:
            raise CommandError(e)
