"""
ServiceBusSender
Sends worklist actions to gateway via Azure Service Bus.
"""

import json
import logging
import os
from datetime import datetime, timezone

from azure.servicebus import ServiceBusClient, ServiceBusMessage

from .models import GatewayAction, GatewayActionStatus

logger = logging.getLogger(__name__)

COMMANDS_QUEUE = os.getenv("SERVICE_BUS_COMMANDS_QUEUE", "worklist-commands")


class ServiceBusSender:
    """Sends worklist actions to gateway via Azure Service Bus queue."""

    def __init__(self):
        self.connection_string = os.getenv("AZURE_SERVICE_BUS_CONNECTION_STRING", "")
        self.queue_name = COMMANDS_QUEUE

    def send_action(self, action: GatewayAction) -> bool:
        try:
            with ServiceBusClient.from_connection_string(
                self.connection_string
            ) as client:
                with client.get_queue_sender(self.queue_name) as sender:
                    message = ServiceBusMessage(
                        body=json.dumps(action.payload),
                        content_type="application/json",
                        message_id=str(action.id),
                    )
                    sender.send_messages(message)

            action.status = GatewayActionStatus.SENT
            action.sent_at = datetime.now(timezone.utc)
            action.save(update_fields=["status", "sent_at"])

            logger.info(f"Action {action.id} sent to {self.queue_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to send action {action.id}: {e}")
            action.status = GatewayActionStatus.FAILED
            action.last_error = str(e)
            action.failed_at = datetime.now(timezone.utc)
            action.save(update_fields=["status", "last_error", "failed_at"])
            return False
