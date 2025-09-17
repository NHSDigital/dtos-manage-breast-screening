from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from manage_breast_screening.notifications.services.blob_storage import BlobStorage
from manage_breast_screening.notifications.services.mesh_inbox import MeshInbox


class Command(BaseCommand):
    """
    Django Admin command which finds Appointment records from MESH Client and sends them
    to Azure Blob Storage.
    """

    def handle(self, *args, **options):
        try:
            today_dirname = datetime.today().strftime("%Y-%m-%d")
            with MeshInbox() as inbox:
                for message_id in inbox.fetch_message_ids():
                    message = inbox.fetch_message(message_id)

                    BlobStorage().add(
                        f"{today_dirname}/{message.filename}",
                        message.read().decode("ASCII"),
                    )

                    inbox.acknowledge(message_id)

        except Exception as e:
            raise CommandError(e)
