import os
from datetime import datetime
from logging import getLogger

import pandas
from django.core.management.base import BaseCommand
from django.db import connection

from manage_breast_screening.notifications.management.commands.helpers.exception_handler import (
    exception_handler,
)
from manage_breast_screening.notifications.models import ZONE_INFO
from manage_breast_screening.notifications.queries.helper import Helper
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

    SMOKE_TEST_BSO_CODE = "SM0K3"
    BSO_CODES = ["MBD", SMOKE_TEST_BSO_CODE]

    REPORTS = [
        ["aggregate", ["3 months"], None],
        ["failures", [datetime.now(tz=ZONE_INFO).date()], "invites_not_sent"],
        ["reconciliation", [datetime.now(tz=ZONE_INFO).date()], None],
    ]

    def handle(self, *args, **options):
        with exception_handler(INSIGHTS_ERROR_NAME):
            logger.info("Create Report Command started")
            for bso_code in self.BSO_CODES:
                for filename, params, report_type in self.REPORTS:
                    dataframe = pandas.read_sql(
                        Helper.sql(filename), connection, params=(params + [bso_code])
                    )

                    csv = dataframe.to_csv(index=False)

                    if not report_type:
                        report_type = filename

                    BlobStorage().add(
                        self.filename(bso_code, report_type),
                        csv,
                        content_type="text/csv",
                        container_name=os.getenv("REPORTS_CONTAINER_NAME"),
                    )

                    NhsMail().send_report_email(
                        attachment_data=csv,
                        attachment_filename=self.filename(bso_code, report_type),
                        report_type=report_type,
                    )

                    logger.info("Report %s created", report_type)

    def filename(self, bso_code: str, report_type: str) -> str:
        formatted_time = datetime.today().strftime("%Y-%m-%dT%H:%M:%S")
        return f"{formatted_time}-{bso_code}-{report_type.replace('_', '-')}-report.csv"
