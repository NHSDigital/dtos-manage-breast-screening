from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas
from django.core.management.base import BaseCommand, CommandError

from manage_breast_screening.notifications.models import (
    Appointment,
    MessageStatusChoices,
)

TZ_INFO = ZoneInfo("Europe/London")
DIR_NAME_DATE_FORMAT = "%Y-%m-%d"


class Command(BaseCommand):
    """
    Django Admin command which creates CSV formatted reports of Appointment notification
    deliveries for the given time period.

    Requires the env vars `BLOB_STORAGE_CONNECTION_STRING` and `BLOB_CONTAINER_NAME`
    to connect to Azure blob storage.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "report_type",
            nargs="?",
            default="failures",
            help="The type of report to be created deliveries|failures",
        )
        parser.add_argument(
            "frequency",
            nargs="?",
            default="daily",
            help="The frequency of the report daily|weekly",
        )

    def handle(self, *args, **options):
        try:
            pandas.read_sql(
                self.sql_for_report(options["report_type"], options["frequency"])
            )

        except Exception as e:
            raise CommandError(e)

    def sql_for_report(self, report_type: str, frequency: str) -> str:
        starts_at = datetime.today().replace(hour=0, minute=0, second=0)
        ends_at = datetime.today().replace(hour=23, minute=59, second=59)

        if frequency == "weekly":
            starts_at = starts_at - timedelta(days=7)

        if report_type == "failures":
            return (
                Appointment.objects.filter(
                    starts_at__gte=starts_at,
                    starts_at__lte=ends_at,
                    message__message_status__status=MessageStatusChoices.FAILED.value,
                )
                .values(
                    "nhs_number",
                    "nbss_id",
                    "starts_at",
                    "message__message_status__description",
                )
                .query.__str__()
            )
