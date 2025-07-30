import os
from datetime import datetime
from functools import cached_property

from azure.storage.blob import BlobServiceClient, ContainerClient
from django.core.management.base import BaseCommand, CommandError
from mesh_client import MeshClient

from manage_breast_screening.notifications.storage import Storage


class Command(BaseCommand):
    """
    Django Admin command which finds Appointment records from MESH Client and sends them
    to Azure Blob Storage.
    """

    def handle(self, *args, **options):
        try:
            client = self.setup()

            all_appointments = client.list_messages()

            for x in all_appointments:
                appointment = client.retrieve_message(x)

                today_dirname = datetime.today().strftime("%Y-%m-%d")

                print(appointment.filename)

                print(appointment.read().decode("ASCII"))

                Storage().add_to_blob_storage(
                    f"{today_dirname}/{appointment.filename}",
                    appointment.read().decode("ASCII"),
                )

        except Exception as e:
            raise CommandError(e)

    def setup(self):
        client = MeshClient(
            url=os.getenv("MESH_BASE_URL"),
            mailbox=os.getenv("MESH_INBOX_NAME"),
            password=os.getenv("MESH_CLIENT_PASSWORD"),
            shared_key=os.getenv("MESH_CLIENT_SHARED_KEY"),
        )
        return client

    @cached_property
    def container_client(self) -> ContainerClient:
        connection_string = os.getenv("BLOB_STORAGE_CONNECTION_STRING")
        container_name = os.getenv("BLOB_CONTAINER_NAME")

        return BlobServiceClient.from_connection_string(
            connection_string
        ).get_container_client(container_name)
