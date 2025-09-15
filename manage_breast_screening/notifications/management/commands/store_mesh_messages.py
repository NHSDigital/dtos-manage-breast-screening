from datetime import datetime
from logging import getLogger

from django.core.management.base import BaseCommand, CommandError

from manage_breast_screening.notifications.services.blob_storage import BlobStorage
from manage_breast_screening.notifications.services.mesh_inbox import MeshInbox

logger = getLogger(__name__)


class Command(BaseCommand):
    """
    Django Admin command which finds Appointment records from MESH Client and sends them
    to Azure Blob Storage.
    """

    def handle(self, *args, **options):
        logger.info("Store MESH Messages Command started")
        try:
            with self.mesh_client() as client:
                today_dirname = datetime.today().strftime("%Y-%m-%d")
                for message in client.list_messages():
                    logger.debug(f"Processing message {message.id}")
                    appointment = client.retrieve_message(message)

                    BlobStorage().add(
                        f"{today_dirname}/{message.filename}",
                        message.read().decode("ASCII"),
                    )

                    logger.info(f"Message {message.id} stored in blob storage")

                    inbox.acknowledge(message_id)

                    logger.info(f"Message {message.id} acknowledged")

        except Exception as e:
            logger.error(e)
            raise CommandError(e)
