import logging
import os

from azure.monitor.opentelemetry.exporter import AzureMonitorMetricExporter
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

logger = logging.getLogger(__name__)


class Metrics:
    def __init__(self, name, units, description, environment):
        try:
            logger.debug(
                (
                    f"Initialising Metrics(name: {name}, units: {units}, "
                    f"description: {description}, environment: {environment})"
                )
            )

            exporter = AzureMonitorMetricExporter(
                connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
            )
            metrics.set_meter_provider(
                MeterProvider(metric_readers=[PeriodicExportingMetricReader(exporter)])
            )
            meter = metrics.get_meter(__name__)
            self.name = name
            self.environment = environment
            self.gauge = meter.create_gauge(
                self.name, unit=units, description=description
            )
        except ValueError as e:
            logger.warning(f"Skipping Azure Monitor setup: {e}")
            self.gauge = None

    def add(self, key, value):
        if self.gauge:
            try:
                self.gauge.set(
                    value,
                    {key: self.name, "environment": self.environment},
                )
            except Exception:
                logger.exception("Failed to update gauge")
