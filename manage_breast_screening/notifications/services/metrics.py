import logging
import os

from azure.monitor.opentelemetry.exporter import AzureMonitorMetricExporter
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

logger = logging.getLogger(__name__)


class Metrics:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        environment = os.getenv("ENVIRONMENT")
        logger.debug((f"Initialising Metrics(environment: {environment})"))

        exporter = AzureMonitorMetricExporter(
            connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
        )
        metrics.set_meter_provider(
            MeterProvider(metric_readers=[PeriodicExportingMetricReader(exporter)])
        )
        self.meter = metrics.get_meter(__name__)
        self.environment = environment

    def set_gauge_value(self, metric_name, units, description, value):
        logger.debug(
            (
                f"Metrics: set_gauge_value(metric_name: {metric_name} "
                f"units: {units}, description: {description}, value: {value})"
            )
        )

        # Create gauge metric
        gauge = self.meter.create_gauge(
            metric_name, unit=units, description=description
        )

        # Set metric value
        gauge.set(
            value,
            {"environment": self.environment},
        )
