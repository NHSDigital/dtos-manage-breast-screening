import os

from azure.core.exceptions import ResourceExistsError
from azure.identity import ManagedIdentityCredential
from azure.storage.queue import QueueClient, QueueMessage


class QueueConfigurationError(Exception):
    """Raised when queue is not properly configured"""

    pass


class Queue:
    def __init__(self, queue_name):
        storage_account_name = os.getenv("STORAGE_ACCOUNT_NAME")
        queue_mi_client_id = os.getenv("QUEUE_MI_CLIENT_ID")
        connection_string = os.getenv("QUEUE_STORAGE_CONNECTION_STRING")

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
        else:
            raise QueueConfigurationError(
                "Queue not configured: Either QUEUE_STORAGE_CONNECTION_STRING or "
                "(STORAGE_ACCOUNT_NAME and QUEUE_MI_CLIENT_ID) must be set"
            )

    def add(self, message: str):
        if not hasattr(self, "client") or self.client is None:
            raise QueueConfigurationError("Queue client not initialized")
        self.client.send_message(message)

    def delete(self, message: str | QueueMessage):
        self.client.delete_message(message)

    def items(self, limit=50):
        return self.client.receive_messages(max_messages=limit)

    def peek(self):
        return self.client.peek_messages()

    def item(self):
        return self.client.receive_message()

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
