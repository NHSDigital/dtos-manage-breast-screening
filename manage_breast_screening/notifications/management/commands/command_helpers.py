from datetime import datetime
from zoneinfo import ZoneInfo

from manage_breast_screening.notifications.models import (
    Message,
    MessageBatch,
)

TZ_INFO = ZoneInfo("Europe/London")

class MessageBatchHelpers():
    @staticmethod
    def mark_batch_as_sent(message_batch: MessageBatch, response_json: dict):
        message_batch.notify_id = response_json["data"]["id"]
        message_batch.sent_at = datetime.now(tz=TZ_INFO)
        message_batch.status = "sent"
        message_batch.save()

        for message_json in response_json["data"]["attributes"]["messages"]:
            message = Message.objects.get(pk=message_json["messageReference"])
            if message:
                message.notify_id = message_json["id"]
                message.status = "delivered"
                message.save()
