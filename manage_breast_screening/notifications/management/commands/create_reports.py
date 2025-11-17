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


class ReportConfig:
    """Config for a report to be generated. Report filename defaults to the query filename if not provided."""

    def __init__(
        self,
        query_filename: str,
        params: list,
        send_email: bool = False,
        report_filename: str | None = None,
    ):
        self.query_filename = query_filename
        self.params = params
        self.send_email = send_email
        self.report_filename = report_filename or query_filename


class Command(BaseCommand):
    """
    Django Admin command which generates and stores CSV report data based on
    common reporting queries.
    Reports are generated sequentially.
    Reports are stored in Azure Blob storage.
    """

    SMOKE_TEST_BSO_CODE = "SM0K3"
    BSO_CODES = ["MBD"]

    REPORTS = [
        ReportConfig("aggregate", ["3 months"], True),
        ReportConfig(
            "failures", [datetime.now(tz=ZONE_INFO).date()], True, "invites_not_sent"
        ),
        ReportConfig("reconciliation", [datetime.now(tz=ZONE_INFO).date()], True),
    ]

    def add_arguments(self, parser):
        parser.add_argument("--smoke-test", action="store_true")

    def handle(self, *args, **options):
        with exception_handler(INSIGHTS_ERROR_NAME):
            logger.info("Create Report Command started")

            bso_codes, report_configs = self.configuration(options)

            for bso_code in bso_codes:
                for report_config in report_configs:
                    dataframe = pandas.read_sql(
                        Helper.sql(report_config.query_filename),
                        connection,
                        params=(report_config.params + [bso_code]),
                    )

                    csv = dataframe.to_csv(index=False)

                    BlobStorage().add(
                        self.filename(bso_code, report_config.report_filename),
                        csv,
                        content_type="text/csv",
                        container_name=os.getenv("REPORTS_CONTAINER_NAME"),
                    )
                    if self.should_send_email(options, report_config):
                        NhsMail().send_report_email(
                            attachment_data=csv,
                            attachment_filename=self.filename(
                                bso_code, report_config.report_filename
                            ),
                            report_type=report_config.report_filename,
                        )

                    logger.info("Report %s created", report_config.report_filename)

    def configuration(self, options: dict) -> tuple[list[str], list[ReportConfig]]:
        if self.is_smoke_test(options):
            reconciliation_report_config = self.REPORTS[2]
            bso_codes = [self.SMOKE_TEST_BSO_CODE]
            report_configs = [reconciliation_report_config]
        else:
            bso_codes = self.BSO_CODES
            report_configs = self.REPORTS

        return bso_codes, report_configs

    def filename(self, bso_code: str, report_type: str) -> str:
        name = f"{bso_code}-{report_type.replace('_', '-')}-report.csv"
        if bso_code != self.SMOKE_TEST_BSO_CODE:
            name = f"{datetime.today().strftime('%Y-%m-%dT%H:%M:%S')}-{name}"
        return name

    def is_smoke_test(self, options):
        return options.get("smoke_test", False)

    def should_send_email(self, options, report_config) -> bool:
        return report_config.send_email and not self.is_smoke_test(options)
