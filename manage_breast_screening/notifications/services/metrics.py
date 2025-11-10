import logging
import os

from azure.monitor.opentelemetry.exporter import AzureMonitorMetricExporter
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

logger = logging.getLogger(__name__)


class Metrics:
    def __init__(
        self, metric_name, metric_units, metric_description, metric_environment
    ):
        self.metric_name = metric_name

        try:
            logger.info(f"metric_name: {metric_name}")
            logger.info(f"metric_units: {metric_units}")
            logger.info(f"metric_description: {metric_description}")
            logger.info(f"metric_environment: {metric_environment}")

            exporter = AzureMonitorMetricExporter(
                connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
            )
            reader = PeriodicExportingMetricReader(exporter)
            metrics.set_meter_provider(MeterProvider(metric_readers=[reader]))
            meter = metrics.get_meter(__name__)
            self.environment = metric_environment
            self.gauge = meter.create_gauge(
                self.metric_name, unit=metric_units, description=metric_description
            )
        except ValueError as e:
            logger.warning(f"Skipping Azure Monitor setup: {e}")
            self.gauge = None

    def add(self, value):
        if self.gauge:
            try:
                self.gauge.set(
                    value,
                    {"queue_name": self.metric_name, "environment": self.environment},
                )
            except Exception:
                logger.exception("Failed to update gauge")
