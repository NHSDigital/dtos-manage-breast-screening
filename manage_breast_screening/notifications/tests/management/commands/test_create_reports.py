from contextlib import contextmanager
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from django.core.management.base import CommandError

from manage_breast_screening.notifications.management.commands.create_reports import (
    Command,
)


class TestCreateReports:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        monkeypatch.setenv("REPORTS_CONTAINER_NAME", "reports")

    @pytest.fixture
    def csv_data(self):
        return "this,that,1,8,1,2,1"

    @pytest.fixture
    def now(self):
        return datetime.today()

    @contextmanager
    def mocked_dependencies(self, dataframe, csv_data, now):
        module = (
            "manage_breast_screening.notifications.management.commands.create_reports"
        )

        with patch(f"{module}.BlobStorage") as mock_storage:
            mock_blob_storage = MagicMock()
            mock_storage.return_value = mock_blob_storage

            with patch(f"{module}.pandas.read_sql") as mock_read_sql:
                mock_read_sql.return_value = dataframe

                with patch(f"{module}.datetime") as mock_datetime:
                    mock_datetime.today.return_value = now

                    with patch(f"{module}.NhsMail") as mock_email:
                        mock_email_service = MagicMock()
                        mock_email.return_value = mock_email_service

                        yield (mock_blob_storage, mock_email_service)

    @pytest.fixture
    def dataframe(self, csv_data):
        df = MagicMock()
        df.to_csv.return_value = csv_data
        return df

    def test_handle_creates_all_reports(self, dataframe, csv_data, now):
        with self.mocked_dependencies(dataframe, csv_data, now) as md:
            Command().handle()

        aggregate_filename = now.strftime("%Y-%m-%dT%H:%M:%S-aggregate-report.csv")
        failures_filename = now.strftime(
            "%Y-%m-%dT%H:%M:%S-invites-not-sent-report.csv"
        )
        reconciliation_filename = now.strftime(
            "%Y-%m-%dT%H:%M:%S-reconciliation-report.csv"
        )

        mock_blob_storage = md[0]
        assert mock_blob_storage.add.call_count == 3
        mock_blob_storage.add.assert_any_call(
            aggregate_filename,
            csv_data,
            content_type="text/csv",
            container_name="reports",
        )
        mock_blob_storage.add.assert_any_call(
            failures_filename,
            csv_data,
            content_type="text/csv",
            container_name="reports",
        )
        mock_blob_storage.add.assert_any_call(
            reconciliation_filename,
            csv_data,
            content_type="text/csv",
            container_name="reports",
        )

        mock_email_service = md[1]
        assert mock_email_service.send_report_email.call_count == 3
        mock_email_service.send_report_email.assert_any_call(
            attachment_data=csv_data,
            attachment_filename=aggregate_filename,
            report_type="aggregate",
        )
        mock_email_service.send_report_email.assert_any_call(
            attachment_data=csv_data,
            attachment_filename=failures_filename,
            report_type="invites_not_sent",
        )
        mock_email_service.send_report_email.assert_any_call(
            attachment_data=csv_data,
            attachment_filename=reconciliation_filename,
            report_type="reconciliation",
        )

    def test_handle_raises_command_error(self, mock_insights_logger):
        with patch(
            "manage_breast_screening.notifications.queries.helper.Helper"
        ) as mock_query:
            mock_query.sql.side_effect = Exception("err")

            with pytest.raises(CommandError):
                Command().handle()

    @pytest.mark.django_db
    def test_calls_insights_logger_if_exception_raised(
        self, mock_insights_logger, commands_module_str
    ):
        an_exception = Exception("'BlobStorage' object has no attribute 'client'")
        with patch(
            f"{commands_module_str}.create_reports.BlobStorage"
        ) as mock_blob_storage:
            mock_blob_storage.side_effect = an_exception
            with pytest.raises(CommandError):
                Command().handle()

                mock_insights_logger.assert_called_with(
                    f"CreateReportsError: {an_exception}"
                )
