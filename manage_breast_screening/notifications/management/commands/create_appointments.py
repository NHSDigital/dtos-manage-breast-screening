import io
import os
from datetime import datetime
from functools import cached_property
from zoneinfo import ZoneInfo

import pandas
from azure.storage.blob import BlobServiceClient, ContainerClient
from django.core.management.base import BaseCommand, CommandError

from manage_breast_screening.notifications.models import Appointment, Clinic

TZ_INFO = ZoneInfo("Europe/London")
DIR_NAME_DATE_FORMAT = "%Y-%m-%d"


class Command(BaseCommand):
    """
    Django Admin command which reads NBSS appointment data from Azure blob storage
    and saves data as Appointment and Clinic records in the database.

    Requires the env vars `BLOB_STORAGE_CONNECTION_STRING` and `BLOB_CONTAINER_NAME`
    to connect to Azure blob storage.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "date_str",
            nargs="?",
            default=datetime.today()
            .replace(tzinfo=TZ_INFO)
            .strftime(DIR_NAME_DATE_FORMAT),
            help="yyy-MM-dd formatted date reflecting the Azure storage directory",
        )

    def handle(self, *args, **options):
        try:
            for blob in self.container_client.list_blobs(
                name_starts_with=options["date_str"]
            ):
                blob_client = self.container_client.get_blob_client(blob)
                blob_content = blob_client.download_blob(
                    max_concurrency=1, encoding="ASCII"
                ).readall()

                data_frame = self.raw_data_to_data_frame(blob_content)

                for idx, row in data_frame.iterrows():
                    clinic, clinic_created = self.find_or_create_clinic(row)
                    if clinic_created:
                        self.stdout.write(f"{clinic} created")

                    appt, appt_created = self.update_or_create_appointment(row, clinic)
                    if appt_created:
                        self.stdout.write(f"{appt} created")
                    else:
                        self.stdout.write(f"{appt} updated")

                self.stdout.write(f"Processed {len(data_frame)} rows from {blob.name}")
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

    def find_or_create_clinic(self, row: dict) -> tuple[Clinic, bool]:
        return Clinic.objects.get_or_create(
            bso_code=row["BSO"],
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

    def update_or_create_appointment(
        self, row: dict, clinic: Clinic
    ) -> tuple[Appointment, bool]:
        status = row["Status"]
        defaults = {
            "number": row["Sequence"],
            "status": status,
        }
        if status == "C":
            defaults.update({
                "cancelled_by": row["Cancelled By"],
            })
        elif status == "B":
            defaults.update({
                "booked_by": row["Booked By"]
            })

        return Appointment.objects.update_or_create(
            nbss_id=row["Appointment ID"],
            nhs_number=row["NHS Num"],
            clinic=clinic,
            starts_at=self.appointment_date_and_time(row),
            defaults=defaults,
        )


    def appointment_date_and_time(self, row: dict) -> datetime:
        dt = datetime.strptime(
            f"{row['Appt Date']} {row['Appt Time']}",
            "%Y%m%d %H%M",
        )
        return dt.replace(tzinfo=TZ_INFO)

    @cached_property
    def container_client(self) -> ContainerClient:
        connection_string = os.getenv("BLOB_STORAGE_CONNECTION_STRING")
        container_name = os.getenv("BLOB_CONTAINER_NAME")

        return BlobServiceClient.from_connection_string(
            connection_string
        ).get_container_client(container_name)
