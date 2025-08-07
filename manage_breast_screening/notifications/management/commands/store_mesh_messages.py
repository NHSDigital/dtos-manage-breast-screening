import os
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from mesh_client import MeshClient

from manage_breast_screening.notifications.blob_storage import BlobStorage


class Command(BaseCommand):
    """
    Django Admin command which finds Appointment records from MESH Client and sends them
    to Azure Blob Storage.
    """

    def handle(self, *args, **options):
        try:
            with self.mesh_client() as client:
                for message in client.list_messages():
                    appointment = client.retrieve_message(message)

                    today_dirname = datetime.today().strftime("%Y-%m-%d")

                    BlobStorage().add(
                        f"{today_dirname}/{appointment.filename}",
                        appointment.read().decode("ASCII"),
                    )

        except Exception as e:
            raise CommandError(e)

    def mesh_client(self):
        client = MeshClient(
            url=os.getenv("MESH_BASE_URL"),
            mailbox=os.getenv("MESH_INBOX_NAME"),
            password=os.getenv("MESH_CLIENT_PASSWORD"),
            shared_key=os.getenv("MESH_CLIENT_SHARED_KEY"),
        )
        return client
