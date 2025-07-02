import io
import os
from datetime import datetime
from functools import cached_property
from zoneinfo import ZoneInfo

import pandas
from azure.storage.blob import BlobServiceClient, ContainerClient
from django.core.management.base import BaseCommand, CommandError

from manage_breast_screening.notifications.models import Appointment, Clinic


class Command(BaseCommand):
    """
    Django Admin command which reads NBSS appointment data from Azure blob storage
    and saves data as Appointment and Clinic records in the database.

    Requires the env vars `BLOB_STORAGE_CONNECTION_STRING` and `BLOB_CONTAINER_NAME`
    to connect to Azure blob storage.
    """

    def handle(self, *args, **options):
        try:
            today_dirname = datetime.today().strftime("%Y-%m-%d")

            for blob in self.container_client().list_blobs(
                name_starts_with=today_dirname
            ):
                blob_client = self.container_client().get_blob_client(blob)
                blob_content = blob_client.download_blob(
                    max_concurrency=1, encoding="ASCII"
                ).readall()

                data_frame = self.raw_data_to_data_frame(blob_content)

                for idx, row in data_frame.iterrows():
                    clinic, clinic_created = self.find_or_create_clinic(row)
                    if clinic_created:
                        self.stdout.write(f"{clinic} created")

                    appt, appt_created = self.find_or_create_appointment(row, clinic)
                    if appt_created:
                        self.stdout.write(f"{appt} created")

                self.stdout.write(f"Processed {data_frame.size} rows from {blob.name}")
        except Exception as e:
            raise CommandError(e)

    def raw_data_to_data_frame(self, raw_data: str) -> pandas.DataFrame:
        return pandas.read_table(
            io.StringIO(raw_data),
            dtype="str",
            encoding="ASCII",
            engine="python",
            header=1,
            sep="|",
            skipfooter=1,
        )

    def find_or_create_clinic(self, row: dict) -> Clinic:
        return Clinic.objects.get_or_create(
            code=row["Clinic Code"],
            defaults={
                "holding_clinic": True if row["Holding Clinic"] == "Y" else False,
                "location_code": row["Location"],
                "name": row["Clinic Name"],
                "alt_name": row["Clinic Name (Let)"],
                "address_line_1": row["Clinic Address 1"],
                "address_line_2": row["Clinic Address 2"],
                "address_line_3": row["Clinic Address 3"],
                "address_line_4": row["Clinic Address 4"],
                "address_line_5": row["Clinic Address 5"],
                "postcode": row["Postcode"],
            },
        )

    def find_or_create_appointment(self, row: dict, clinic: Clinic) -> Appointment:
        return Appointment.objects.get_or_create(
            nhs_number=row["NHS Num"],
            nbss_id=row["Appointment ID"],
            defaults={
                "clinic": clinic,
                "starts_at": self.appointment_date_and_time(row),
                "number": row["Sequence"],
                "status": row["Status"],
                "booked_by": row["Booked By"],
                "cancelled_by": row["Cancelled By"],
            },
        )

    def appointment_date_and_time(self, row: dict) -> datetime:
        dt = datetime.strptime(
            f"{row['Appt Date']} {row['Appt Time']}",
            "%Y%m%d %H%M",
        )
        return dt.replace(tzinfo=ZoneInfo("Europe/London"))

    @cached_property
    def blob_service_client(self) -> BlobServiceClient:
        connection_string = os.getenv("BLOB_STORAGE_CONNECTION_STRING")
        return BlobServiceClient.from_connection_string(connection_string)

    @cached_property
    def container_client(self) -> ContainerClient:
        container_name = os.getenv("BLOB_CONTAINER_NAME")
        return self.blob_service_client().get_container_client(container_name)
