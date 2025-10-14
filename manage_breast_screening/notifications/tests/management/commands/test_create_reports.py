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

                    yield (mock_blob_storage,)

    @pytest.fixture
    def dataframe(self, csv_data):
        df = MagicMock()
        df.to_csv.return_value = csv_data
        return df

    def test_handle_creates_all_reports(self, dataframe, csv_data, now):
        with self.mocked_dependencies(dataframe, csv_data, now) as md:
            Command().handle()

        mock_blob_storage = md[0]
        mock_blob_storage.add.assert_any_call(
            now.strftime("%Y-%m-%dT%H:%M:%S-aggregate-report.csv"),
            csv_data,
            content_type="text/csv",
            container_name="reports",
        )
        mock_blob_storage.add.assert_any_call(
            now.strftime("%Y-%m-%dT%H:%M:%S-failures-report.csv"),
            csv_data,
            content_type="text/csv",
            container_name="reports",
        )

    def test_handle_raises_command_error(self):
        with patch(
            "manage_breast_screening.notifications.queries.failures_query.FailuresQuery"
        ) as mock_query:
            mock_query.sql.side_effect = Exception("err")

            with pytest.raises(CommandError):
                Command().handle()
