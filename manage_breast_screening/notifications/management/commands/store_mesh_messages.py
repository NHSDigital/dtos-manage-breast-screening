from datetime import datetime
from logging import getLogger

from django.core.management.base import BaseCommand

from manage_breast_screening.notifications.management.commands.helpers.command_handler import (
    CommandHandler,
)
from manage_breast_screening.notifications.services.blob_storage import BlobStorage
from manage_breast_screening.notifications.services.mesh_inbox import MeshInbox

logger = getLogger(__name__)
INSIGHTS_JOB_NAME = "StoreMeshMessages"


class Command(BaseCommand):
    """
    Django Admin command which finds Appointment records from MESH Client and sends them
    to Azure Blob Storage.
    """

    def handle(self, *args, **options):
        with CommandHandler.handle(INSIGHTS_JOB_NAME):
            logger.info("Store MESH Messages command started")
            today_dirname = datetime.today().strftime("%Y-%m-%d")
            with MeshInbox() as inbox:
                for message_id in inbox.fetch_message_ids():
                    logger.debug("Processing message %s", message_id)
                    message = inbox.fetch_message(message_id)

                    BlobStorage().add(
                        f"{today_dirname}/{message.filename}",
                        message.read().decode("ASCII"),
                    )

                    logger.info("Message %s stored in blob storage", message_id)

                    inbox.acknowledge(message_id)

                    logger.info("Message %s acknowledged", message_id)
