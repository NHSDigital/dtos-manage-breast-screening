import os

from azure.core.exceptions import ResourceExistsError
from azure.storage.queue import QueueClient


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

    @classmethod
    def MessageStatusUpdates(cls):
        return cls("message_status_updates")
