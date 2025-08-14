import os

from azure.core.exceptions import ResourceExistsError
from azure.storage.queue import QueueClient, QueueMessage


class Queue:
    def __init__(self, queue_name):
        try:
            self.client = QueueClient.from_connection_string(
                os.getenv("QUEUE_STORAGE_CONNECTION_STRING"), queue_name
            )
            self.client.create_queue()
        except ResourceExistsError:
            pass

    def add(self, message: str):
        self.client.send_message(message)

    def delete(self, message: str | QueueMessage):
        self.client.delete_message(message)

    def items(self, limit=50):
        return self.client.receive_messages(max_messages=limit)

    def peek(self):
        return self.client.peek_messages()

    @classmethod
    def MessageStatusUpdates(cls):
        return cls("message-status-updates")

    @classmethod
    def RetryMessageBatches(cls):
        return cls("retry_message_batches")
