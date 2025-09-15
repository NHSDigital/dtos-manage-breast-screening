import os
from datetime import datetime
from logging import getLogger

import pandas
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from manage_breast_screening.notifications.queries.aggregate_query import AggregateQuery
from manage_breast_screening.notifications.queries.failures_query import FailuresQuery
from manage_breast_screening.notifications.services.blob_storage import BlobStorage

logger = getLogger(__name__)


class Command(BaseCommand):
    """
    Django Admin command which generates and stores CSV report data based on
    common reporting queries:
    'aggregate' covers all notifications sent, failures and deliveries counts
    grouped by appointment date, clinic code and bso code. This report covers
    a 3 month time period and can be resource intensive.
    'failures' covers all failed status updates from NHS Notify and contains
    NHS numbers, Clinic and BSO code and failure dates and reasons for one day.
    If no report_type argument is specified the default behaviour is to
    generate the failures report.
    Reports are stored in Azure Blob storage.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "report_type",
            default="failures",
            help="type of report. Can be 'aggregate' or 'failures'. Default: failures",
        )

    def handle(self, *args, **options):
        logger.info("Create Report Command started")

        report_type = options.get("report_type", "failures")
        try:
            if report_type == "aggregate":
                query = AggregateQuery
                params = ("3 months",)
            else:
                query = FailuresQuery
                params = None

            dataframe = pandas.read_sql(
                query.sql(), connection, params=params, columns=query.columns()
            )

            BlobStorage().add(
                self.filename(report_type),
                dataframe.to_csv(),
                content_type="text/csv",
                container_name=os.getenv("REPORTS_CONTAINER_NAME"),
            )
            logger.info(f"Report {report_type} created")
        except Exception as e:
            logger.error(e)
            raise CommandError(e)

    def filename(self, report_type: str) -> str:
        formatted_time = datetime.today().strftime("%Y-%m-%dT%H:%M:%S")
        return f"{formatted_time}-{report_type}-report.csv"
