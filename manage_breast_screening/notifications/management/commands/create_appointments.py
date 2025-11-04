import io
import os
from datetime import datetime
from logging import getLogger

import pandas
from django.core.management.base import BaseCommand

from manage_breast_screening.notifications.management.commands.helpers.exception_handler import (
    exception_handler,
)
from manage_breast_screening.notifications.models import (
    ZONE_INFO,
    Appointment,
    AppointmentStatusChoices,
    Clinic,
)
from manage_breast_screening.notifications.services.blob_storage import BlobStorage

DIR_NAME_DATE_FORMAT = "%Y-%m-%d"
INSIGHTS_ERROR_NAME = "CreateAppointmentsError"
logger = getLogger(__name__)


class Command(BaseCommand):
    """
    Django Admin command which reads NBSS appointment data from Azure blob storage
    and saves data as Appointment and Clinic records in the database.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "date_str",
            nargs="?",
            default=datetime.now(tz=ZONE_INFO).strftime(DIR_NAME_DATE_FORMAT),
            help="yyy-MM-dd formatted date reflecting the Azure storage directory",
        )

    def handle(self, *args, **options):
        with exception_handler(INSIGHTS_ERROR_NAME):
            logger.info("Create Appointments command started")
            container_client = BlobStorage().find_or_create_container(
                os.getenv("BLOB_CONTAINER_NAME", "")
            )
            for blob in container_client.list_blobs(
                name_starts_with=options["date_str"]
            ):
                blob_client = container_client.get_blob_client(blob.name)
                logger.debug("Processing blob %s", blob.name)
                blob_content = blob_client.download_blob(
                    max_concurrency=1, encoding="ASCII"
                ).readall()

                data_frame = self.raw_data_to_data_frame(blob_content)

                for idx, row in data_frame.iterrows():
                    if self.is_not_holding_clinic(row):
                        clinic, clinic_created = self.find_or_create_clinic(row)
                        if clinic_created:
                            logger.info("%s created", clinic)

                        appt, appt_created = self.update_or_create_appointment(
                            row, clinic, blob.name
                        )
                logger.info("Processed %s rows from %s", len(data_frame), blob.name)
            logger.info("Create Appointments command finished successfully")

    def is_not_holding_clinic(self, row):
        return row.get("Holding Clinic") != "Y"

    def raw_data_to_data_frame(self, raw_data: str) -> pandas.DataFrame:
        return pandas.read_table(
            io.StringIO(raw_data),
            dtype="str",
            encoding="ASCII",
            engine="python",
            header=1,
            keep_default_na=False,
            sep="|",
            skipfooter=1,
        )

    def find_or_create_clinic(self, row: pandas.Series) -> tuple[Clinic, bool]:
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
        self, row: pandas.Series, clinic: Clinic, extract: str
    ) -> tuple[Appointment | None, bool]:
        appointment = Appointment.objects.filter(nbss_id=row["Appointment ID"]).first()

        if self.is_new_booking(row, appointment):
            new_appointment = Appointment.objects.create(
                nbss_id=row["Appointment ID"],
                nhs_number=row["NHS Num"],
                number=row["Screen Appt num"],
                batch_id=self.handle_aliased_column("Batch ID", "BatchID", row),
                clinic=clinic,
                episode_started_at=datetime.strptime(
                    row["Episode Start"], "%Y%m%d"
                ).replace(tzinfo=ZONE_INFO),
                episode_type=self.handle_aliased_column(
                    "Episode Type", "Epsiode Type", row
                ),
                starts_at=self.appointment_date_and_time(row),
                status=row["Status"],
                booked_by=row["Booked By"],
                booked_at=self.workflow_action_date_and_time(row["Action Timestamp"]),
                assessment=(
                    self.handle_aliased_column(
                        "Screen or Assess", "Screen or Asses", row
                    )
                    == "A"
                ),
                extract=extract,
            )
            logger.info("%s created", new_appointment)
            return (new_appointment, True)
        elif self.is_cancelling_existing_appointment(row, appointment):
            appointment.status = AppointmentStatusChoices.CANCELLED.value
            appointment.cancelled_by = row["Cancelled By"]
            appointment.cancelled_at = self.workflow_action_date_and_time(
                row["Action Timestamp"]
            )
            appointment.save()
            logger.info("%s cancelled", appointment)
        elif self.is_completed_appointment(row, appointment):
            appointment.status = row["Status"]
            appointment.attended_not_screened = row["Attended Not Scr"]
            appointment.completed_at = self.workflow_action_date_and_time(
                row["Action Timestamp"]
            )
            appointment.save()
            logger.info("%s marked completed (%s)", appointment, row.get("Status"))
        elif appointment is None:
            logger.info(
                "No Appointment record found for NBSS ID: %s", row.get("Appointment ID")
            )

        return (appointment, False)

    def is_cancelling_existing_appointment(self, row, appointment: Appointment):
        return appointment is not None and row["Status"] == "C"

    def is_new_booking(self, row, appointment: Appointment):
        return appointment is None and row["Status"] == "B"

    def is_completed_appointment(self, row, appointment: Appointment):
        return (
            appointment is not None
            and row["Status"] in ["A", "D"]
            and appointment.starts_at < datetime.now(tz=ZONE_INFO)
        )

    def workflow_action_date_and_time(self, timestamp: str) -> datetime:
        dt = datetime.strptime(timestamp, "%Y%m%d-%H%M%S")
        return dt.replace(tzinfo=ZONE_INFO)

    def handle_aliased_column(
        self, expected_name: str, fallback_name: str, row: pandas.Series
    ) -> object:
        return row.get(expected_name, row.get(fallback_name))

    def appointment_date_and_time(self, row: pandas.Series) -> datetime:
        dt = datetime.strptime(
            f"{row['Appt Date']} {row['Appt Time']}",
            "%Y%m%d %H%M",
        )
        return dt.replace(tzinfo=ZONE_INFO)
