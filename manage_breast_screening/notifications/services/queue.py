import logging
import os

from azure.monitor.opentelemetry.exporter import AzureMonitorMetricExporter
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

logger = logging.getLogger(__name__)

class Queue:
    def __init__(self, queue_name):
        logger.exception("init Queue")
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

        exporter = AzureMonitorMetricExporter(connection_string=os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"])
        reader = PeriodicExportingMetricReader(exporter)
        metrics.set_meter_provider(MeterProvider(metric_readers=[reader]))
        self.meter = metrics.get_meter(__name__)
        self.gauge = self.meter.create_gauge(self.queue_name, unit="messages", description="Queue length")

        self.metrics()

    def add(self, message: str):
        self.client.send_message(message)
        self.metrics()

    def delete(self, message: str | QueueMessage):
        self.client.delete_message(message)
        self.metrics()

    def items(self, limit=50):
        return self.client.receive_messages(max_messages=limit)

    def peek(self):
        return self.client.peek_messages()

    def item(self):
        return self.client.receive_message()

    def metrics(self):
        logger.exception("record the metrics")
        try:
            properties = self.client.get_queue_properties()
            self.message_count = properties.approximate_message_count
        except Exception as e:
            logger.exception(e)
            self.message_count = None
            return

        try:
            print(f"Reporting queue size: {self.message_count}")
            self.gauge.set(self.message_count, {"queue_name": self.queue_name})

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
