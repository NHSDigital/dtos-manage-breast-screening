import logging
import os

from azure.monitor.opentelemetry import configure_azure_monitor
from django.core.management.base import BaseCommand


def getLogger():
    if os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING") is not None:
        # Configure OpenTelemetry to use Azure Monitor with the
        # APPLICATIONINSIGHTS_CONNECTION_STRING environment variable.
        configure_azure_monitor(
            # Set the namespace for the logger in which you would like to collect telemetry for if you are collecting logging telemetry. This is imperative so you do not collect logging telemetry from the SDK itself.
            logger_name="manbrs",
        )
        # Logging telemetry will be collected from logging calls made with this logger and all of it's children loggers.
        return logging.getLogger("manbrs")
    else:
        return logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django Admin command which takes an ID of a MessageBatch with
    a failed status and retries sending it to the Communications API.
    """

    def handle(self, *args, **options):
        logger = getLogger()
        # Log a custom event with a custom name and additional attribute
        # The 'microsoft.custom_event.name' value will be used as the name of the customEvent
        logger.warning(
            "Hello World!",
            extra={
                "microsoft.custom_event.name": "test-event-name",
                "additional_attrs": "val1",
            },
        )

        logger.info("info log")
        logger.warning("warning log")
        logger.error("error log", stack_info=True, exc_info=True)
        raise Exception("test error")

    # logger.info("No messages on queue")
    #     return

    # message_batch_id = json.loads(queue_message.content)["message_batch_id"]
    # message_batch = MessageBatch.objects.filter(
    #     id=message_batch_id,
    #     status=MessageBatchStatusChoices.FAILED_RECOVERABLE.value,
    # ).first()

    # if message_batch is None:
    #     raise CommandError(
    #         f"Message Batch with id {message_batch_id} and status of '{MessageBatchStatusChoices.FAILED_RECOVERABLE.value}' not found"
    #     )

    # queue.delete(queue_message)

    # retry_count = int(json.loads(queue_message.content)["retry_count"])
    # if retry_count < int(os.getenv("NOTIFICATIONS_BATCH_RETRY_LIMIT", "5")):
    #     time.sleep(
    #         int(os.getenv("NOTIFICATIONS_BATCH_RETRY_DELAY", "0")) * retry_count
    #     )

    #     try:
    #         response = ApiClient().send_message_batch(message_batch)

    #         if response.status_code == 201:
    #             MessageBatchHelpers.mark_batch_as_sent(
    #                 message_batch=message_batch, response_json=response.json()
    #             )
    #         else:
    #             MessageBatchHelpers.mark_batch_as_failed(
    #                 message_batch=message_batch,
    #                 response=response,
    #                 retry_count=(retry_count + 1),
    #             )

    # except Exception as e:
    #     raise CommandError(e)
    # else:
    #     message_batch.status = MessageBatchStatusChoices.FAILED_UNRECOVERABLE.value
    #     message_batch.save()
    #     raise CommandError(
    #         f"Message Batch with id {message_batch_id} not sent: Retry limit exceeded"
    #     )
