import os
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from mesh_client import MeshClient

from manage_breast_screening.notifications.tests.integration.helpers import Helpers


class Command(BaseCommand):
    """
    Django Admin command which finds Appointment records from MESH Client and sends them
    to Azure Blob Storage.
    """

    def add_arguments(self, parser):
        parser.add_argument("appointment_id")

    def handle(self, *args, **options):
        try:
            client = self.setup()
            appointment = self.get_appointment_details(
                client, options["appointment_id"]
            )

            today_dirname = datetime.today().strftime("%Y-%m-%d")

            Helpers().add_to_blob_storage(
                f"{today_dirname}/test.dat", appointment.read()
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

    def get_appointment_details(self, client: MeshClient, appointment_id: str) -> dict:
        appointment = client.retrieve_message(appointment_id)
        return appointment
