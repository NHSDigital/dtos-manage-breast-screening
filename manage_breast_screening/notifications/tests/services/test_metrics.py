from unittest.mock import MagicMock, patch

import pytest

from manage_breast_screening.notifications.services.metrics import Metrics


class TestMetrics:
    @pytest.fixture
    def conn_string(self):
        return "InstrumentationKey=00000000-0000-0000-0000-000000000000"

    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch, conn_string):
        monkeypatch.setenv("APPLICATIONINSIGHTS_CONNECTION_STRING", conn_string)

    @patch(
        "manage_breast_screening.notifications.services.metrics.AzureMonitorMetricExporter"
    )
    @patch(
        "manage_breast_screening.notifications.services.metrics.PeriodicExportingMetricReader"
    )
    @patch("manage_breast_screening.notifications.services.metrics.metrics")
    @patch("manage_breast_screening.notifications.services.metrics.MeterProvider")
    def test_metrics_initialisation(
        self,
        mock_meter_provider,
        mock_metrics,
        mock_metric_reader,
        mock_metric_exporter,
        conn_string,
    ):
        mock_meter = MagicMock()
        mock_metrics.get_meter.return_value = mock_meter

        subject = Metrics(environment="dev")

        mock_metric_exporter.assert_called_once_with(connection_string=str(conn_string))
        mock_metric_reader.assert_called_once_with(mock_metric_exporter.return_value)
        mock_meter_provider.assert_called_once_with(
            metric_readers=[mock_metric_reader.return_value]
        )
        mock_metrics.set_meter_provider.assert_called_once_with(
            mock_meter_provider.return_value
        )
        mock_metrics.get_meter.assert_called_once_with(
            "manage_breast_screening.notifications.services.metrics"
        )

        assert subject.meter == mock_meter
        assert subject.environment == "dev"

    @patch(
        "manage_breast_screening.notifications.services.metrics.AzureMonitorMetricExporter"
    )
    @patch(
        "manage_breast_screening.notifications.services.metrics.PeriodicExportingMetricReader"
    )
    @patch("manage_breast_screening.notifications.services.metrics.metrics")
    @patch("manage_breast_screening.notifications.services.metrics.MeterProvider")
    def test_set_gauge_value(
        self,
        mock_meter_provider,
        mock_metrics,
        mock_reader,
        mock_exporter,
    ):
        mock_meter = MagicMock()
        mock_gauge = MagicMock()

        mock_metrics.get_meter.return_value = mock_meter
        mock_meter.create_gauge.return_value = mock_gauge

        subject = Metrics(environment="prod")

        subject.set_gauge_value(
            metric_name="queue_depth",
            units="messages",
            description="Number of messages",
            value=999,
        )

        mock_meter.create_gauge.assert_called_once_with(
            "queue_depth",
            unit="messages",
            description="Number of messages",
        )

        mock_gauge.set.assert_called_once_with(
            999,
            {"environment": "prod"},
        )
