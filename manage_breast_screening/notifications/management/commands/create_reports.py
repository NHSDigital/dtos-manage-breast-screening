import os
from datetime import datetime
from logging import getLogger

import pandas
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from manage_breast_screening.notifications.queries.helper import Helper
from manage_breast_screening.notifications.services.application_insights_logging import (
    ApplicationInsightsLogging,
)
from manage_breast_screening.notifications.services.blob_storage import BlobStorage
from manage_breast_screening.notifications.services.nhs_mail import NhsMail

logger = getLogger(__name__)
INSIGHTS_ERROR_NAME = "CreateReportsError"


class Command(BaseCommand):
    """
    Django Admin command which generates and stores CSV report data based on
    common reporting queries:
    'aggregate' covers all notifications sent, failures and deliveries counts
    grouped by appointment date, clinic code and bso code. This report covers
    a 3 month time period and can be resource intensive.
    'failures' covers all failed status updates from NHS Notify and contains
    NHS numbers, Clinic and BSO code and failure dates and reasons for one day.
    Reports are generated sequentially.
    Reports are stored in Azure Blob storage.
    """

    REPORTS = [
        ["aggregate", ("3 months",), "aggregate"],
        ["failures", (datetime.now(),), "invites_not_sent"],
    ]

    def handle(self, *args, **options):
        logger.info("Create Report Command started")
        try:
            for sqlfile, params, report_type in self.REPORTS:
                dataframe = pandas.read_sql(
                    Helper.sql(sqlfile), connection, params=params
                )

                csv = dataframe.to_csv(index=False)

                BlobStorage().add(
                    self.filename(report_type),
                    csv,
                    content_type="text/csv",
                    container_name=os.getenv("REPORTS_CONTAINER_NAME"),
                )

                NhsMail().send_report_email(
                    attachment_data=csv,
                    attachment_filename=self.filename(report_type),
                    report_type=report_type,
                )

                logger.info("Report %s created", report_type)
        except Exception as e:
            ApplicationInsightsLogging().exception(f"{INSIGHTS_ERROR_NAME}: {e}")
            raise CommandError(e)

    def filename(self, report_type: str) -> str:
        formatted_time = datetime.today().strftime("%Y-%m-%dT%H:%M:%S")
        return f"{formatted_time}-{report_type.replace('_', '-')}-report.csv"
