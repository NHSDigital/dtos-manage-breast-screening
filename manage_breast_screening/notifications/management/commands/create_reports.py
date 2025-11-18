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
        name: str,
        params: list,
        send_email: bool = False,
        query: str | None = None,
    ):
        self.name = name
        self.params = params
        self.send_email = send_email
        self.query = query or name


class Command(BaseCommand):
    """
    Django Admin command which generates and stores CSV report data based on
    common reporting queries.
    Reports are generated sequentially.
    Reports are stored in Azure Blob storage.
    """

    BSO_CODES = ["MBD"]
    REPORTS = [
        ReportConfig("aggregate", ["3 months"], True),
        ReportConfig(
            "invites-not-sent", [datetime.now(tz=ZONE_INFO).date()], True, "failures"
        ),
        ReportConfig("reconciliation", [datetime.now(tz=ZONE_INFO).date()], True),
    ]
    SMOKE_TEST_BSO_CODE = "SM0K3"
    SMOKE_TEST_CONFIG = ReportConfig(
        "reconciliation", [datetime.now(tz=ZONE_INFO).date()], False
    )

    def add_arguments(self, parser):
        parser.add_argument("--smoke-test", action="store_true")

    def handle(self, *args, **options):
        with exception_handler(INSIGHTS_ERROR_NAME):
            logger.info("Create Report Command started")

            bso_codes, report_configs = self.configuration(options)
            external_reports = {}

            for bso_code in bso_codes:
                for report_config in report_configs:
                    dataframe = pandas.read_sql(
                        Helper.sql(report_config.query),
                        connection,
                        params=(report_config.params + [bso_code]),
                    )

                    csv = dataframe.to_csv(index=False)
                    filename = self.filename(bso_code, report_config.name)

                    BlobStorage().add(filename, csv, content_type="text/csv")

                    if report_config.send_email:
                        external_reports[filename] = csv

                    logger.info("Report %s created", report_config.name)

            if bool(external_reports):
                NhsMail().send_reports_email(external_reports)
                logger.info(f"Reports sent: {', '.join(external_reports.keys())}")

            logger.info("Create Report Command finished")

    def configuration(self, options: dict) -> tuple[list[str], list[ReportConfig]]:
        if options.get("smoke_test", False):
            bso_codes = [self.SMOKE_TEST_BSO_CODE]
            report_configs = [self.SMOKE_TEST_CONFIG]
        else:
            bso_codes = self.BSO_CODES
            report_configs = self.REPORTS

        return bso_codes, report_configs

    def filename(self, bso_code: str, report_type: str) -> str:
        name = f"{bso_code}-{report_type}-report.csv"
        if bso_code != self.SMOKE_TEST_BSO_CODE:
            name = f"{datetime.today().strftime('%Y-%m-%dT%H:%M:%S')}-{name}"
        return name
