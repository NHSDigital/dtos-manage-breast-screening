import logging
import os

from azure.core.exceptions import ResourceExistsError
from azure.identity import ManagedIdentityCredential
from azure.storage.queue import QueueClient, QueueMessage
from opentelemetry.metrics import get_meter_provider

logger = logging.getLogger(__name__)


class Queue:
    def __init__(self, queue_name):
        storage_account_name = os.getenv("STORAGE_ACCOUNT_NAME")
        queue_mi_client_id = os.getenv("QUEUE_MI_CLIENT_ID")
        connection_string = os.getenv("QUEUE_STORAGE_CONNECTION_STRING")
        self.queue_name = queue_name

        if storage_account_name and queue_mi_client_id:
            self.client = QueueClient(
                f"https://{storage_account_name}.queue.core.windows.net",
                queue_name=queue_name,
                credential=ManagedIdentityCredential(client_id=queue_mi_client_id),
            )

        elif connection_string:
            try:
                self.client = QueueClient.from_connection_string(
                    connection_string, queue_name
                )
                self.client.create_queue()
            except ResourceExistsError:
                pass

        self.metrics()

    def add(self, message: str):
        self.client.send_message(message)

    def delete(self, message: str | QueueMessage):
        self.client.delete_message(message)

    def items(self, limit=50):
        return self.client.receive_messages(max_messages=limit)

    def peek(self):
        return self.client.peek_messages()

    def item(self):
        return self.client.receive_message()

    def metrics(self):
        try:
            properties = self.client.get_queue_properties()
            self.message_count = properties.approximate_message_count
        except Exception as e:
            logger.exception(e)
            self.message_count = None
            return None

        try:
            meter = get_meter_provider().get_meter("queue_metrics")

            gauge = meter.create_gauge(
                name=self.queue_name,
                description="Approximate number of messages in the queue",
                unit="messages",
            )

            if self.message_count is not None:
                gauge.record(self.message_count)

        except Exception as e:
            logger.exception(e)

        return self.message_count

    @classmethod
    def MessageStatusUpdates(cls):
        return cls(
            os.getenv(
                "STATUS_UPDATES_QUEUE_NAME", "notifications-message-status-updates"
            )
        )

    @classmethod
    def RetryMessageBatches(cls):
        return cls(os.getenv("RETRY_QUEUE_NAME", "notifications-message-batch-retries"))
