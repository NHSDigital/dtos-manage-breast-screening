from contextlib import contextmanager
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from django.core.management.base import CommandError
from django.db import connection

from manage_breast_screening.notifications.management.commands.create_reports import (
    Command,
    ReportConfig,
)
from manage_breast_screening.notifications.queries.helper import Helper


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
        with patch(f"{Command.__module__}.BlobStorage") as mock_storage:
            mock_blob_storage = MagicMock()
            mock_storage.return_value = mock_blob_storage

            with patch(f"{Command.__module__}.pandas.read_sql") as mock_read_sql:
                mock_read_sql.return_value = dataframe

                with patch(f"{Command.__module__}.datetime") as mock_datetime:
                    mock_datetime.today.return_value = now

                    with patch(f"{Command.__module__}.NhsMail") as mock_email:
                        mock_email_service = MagicMock()
                        mock_email.return_value = mock_email_service

                        yield (mock_read_sql, mock_blob_storage, mock_email_service)

    @pytest.fixture
    def dataframe(self, csv_data):
        df = MagicMock()
        df.to_csv.return_value = csv_data
        return df

    def test_handle_creates_all_reports(self, dataframe, csv_data, now):
        with self.mocked_dependencies(dataframe, csv_data, now) as md:
            Command().handle()

        mock_read_sql, mock_blob_storage, mock_email_service = md

        assert mock_read_sql.call_count == 2
        assert mock_blob_storage.add.call_count == 2
        assert mock_email_service.send_reports_email.call_count == 1

        for bso_code in Command.BSO_CODES:
            mock_read_sql.assert_any_call(
                Helper.sql("failures"), connection, params=[now.date(), bso_code]
            )
            mock_read_sql.assert_any_call(
                Helper.sql("reconciliation"), connection, params=["3 months", bso_code]
            )

            failures_filename = f"{now.strftime('%Y-%m-%dT%H:%M:%S')}-{bso_code}-invites-not-sent-report.csv"
            reconciliation_filename = f"{now.strftime('%Y-%m-%dT%H:%M:%S')}-{bso_code}-reconciliation-report.csv"

            mock_blob_storage.add.assert_any_call(
                failures_filename,
                csv_data,
                content_type="text/csv",
            )
            mock_blob_storage.add.assert_any_call(
                reconciliation_filename,
                csv_data,
                content_type="text/csv",
            )

            mock_email_service.send_reports_email.assert_called_once_with(
                {
                    failures_filename: csv_data,
                    reconciliation_filename: csv_data,
                }
            )

    def test_handle_raises_command_error(self, mock_insights_logger):
        with patch(f"{Helper.__module__}.Helper") as mock_query:
            mock_query.sql.side_effect = Exception("err")

            with pytest.raises(CommandError):
                Command().handle()

    @pytest.mark.django_db
    def test_calls_insights_logger_if_exception_raised(self, mock_insights_logger):
        an_exception = Exception("'BlobStorage' object has no attribute 'client'")
        with patch(f"{Command.__module__}.BlobStorage") as mock_blob_storage:
            mock_blob_storage.side_effect = an_exception
            with pytest.raises(CommandError):
                Command().handle()

                mock_insights_logger.assert_called_with(
                    f"CreateReportsError: {an_exception}"
                )

    @pytest.mark.django_db
    def test_calls_command_handler(
        self,
        dataframe,
        csv_data,
        now,
        mock_command_handler,
    ):
        with self.mocked_dependencies(dataframe, csv_data, now):
            Command().handle()
        mock_command_handler.assert_called_with("CreateReports")

    @pytest.mark.django_db
    def test_smoke_test_argument_uses_correct_configuration(
        self, dataframe, csv_data, now
    ):
        with self.mocked_dependencies(dataframe, csv_data, now) as md:
            Command().handle(**{"smoke_test": True})

        mock_read_sql, mock_blob_storage, mock_email_service = md

        mock_read_sql.assert_called_once_with(
            Helper.sql("reconciliation"), connection, params=["1 week", "SM0K3"]
        )
        mock_blob_storage.add.assert_called_once_with(
            "SM0K3-reconciliation-report.csv",
            csv_data,
            content_type="text/csv",
        )
        mock_email_service.assert_not_called()

    def test_handle_does_not_email_reports_with_send_email_false(
        self, dataframe, csv_data, now, monkeypatch
    ):
        """
        Test that internal reports are not emailed but still stored.
        """
        test_reports = [
            ReportConfig("external-report", [now.date()], True),
            ReportConfig("internal-report", [now.date()], False),
        ]
        monkeypatch.setattr(Command, "REPORTS", test_reports)

        with patch(f"{Helper.__module__}.Helper.sql") as mock_helper_sql:
            mock_helper_sql.return_value = "SELECT 1"

            with self.mocked_dependencies(dataframe, csv_data, now) as md:
                Command().handle()

            mock_read_sql, mock_blob_storage, mock_email_service = md

            assert mock_read_sql.call_count == 2
            assert mock_blob_storage.add.call_count == 2
            assert mock_email_service.send_reports_email.call_count == 1

            internal_filename = (
                f"{now.strftime('%Y-%m-%dT%H:%M:%S')}-MBD-internal-report-report.csv"
            )
            external_filename = (
                f"{now.strftime('%Y-%m-%dT%H:%M:%S')}-MBD-external-report-report.csv"
            )
            mock_blob_storage.add.assert_any_call(
                internal_filename,
                csv_data,
                content_type="text/csv",
            )
            mock_blob_storage.add.assert_any_call(
                external_filename,
                csv_data,
                content_type="text/csv",
            )

            mock_email_service.send_reports_email.assert_called_once_with(
                {external_filename: csv_data}
            )

    def test_handle_with_internal_reports_does_not_call_email_service(
        self, dataframe, csv_data, now, monkeypatch
    ):
        """
        Test that internal reports are not emailed but still stored.
        """
        monkeypatch.setattr(
            Command, "REPORTS", [ReportConfig("internal-report", [1], False)]
        )

        with patch(f"{Helper.__module__}.Helper.sql") as mock_helper_sql:
            mock_helper_sql.return_value = "SELECT 1"

            with self.mocked_dependencies(dataframe, csv_data, now) as md:
                Command().handle()

            mock_read_sql, mock_blob_storage, mock_email_service = md

            assert mock_read_sql.call_count == 1
            assert mock_blob_storage.add.call_count == 1
            assert mock_email_service.send_reports_email.call_count == 0
