# delme.py
import logging
import os
import time

from azure.monitor.opentelemetry.exporter import AzureMonitorMetricExporter
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    MetricReader,
    PeriodicExportingMetricReader,
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MyPushReader(MetricReader):
    """
    Concrete MetricReader that exports when we call provider.force_flush().
    NOTE: _receive_metrics accepts timeout_millis and **kwargs to match MeterProvider.force_flush().
    """

    def __init__(self, exporter):
        super().__init__()
        self._exporter = exporter

    # Accept timeout_millis and any other kwargs to avoid TypeError
    def _receive_metrics(self, metrics_data, timeout_millis: int = None, **kwargs):
        logger.debug(
            "MyPushReader._receive_metrics called (timeout_millis=%s, other=%s)",
            timeout_millis,
            kwargs,
        )
        try:
            # exporter.export expects the metrics_data object produced by the SDK
            self._exporter.export(metrics_data)
        except Exception:
            logger.exception("Failed to export metrics")

    def flush(self):
        """Manual flush method."""
        logger.debug("MyPushReader.flush called")
        try:
            self._exporter.force_flush()
        except Exception:
            logger.exception("Failed to flush exporter")

    def shutdown(self, timeout_millis: int = None):
        logger.debug("MyPushReader.shutdown called (timeout_millis=%s)", timeout_millis)
        try:
            if hasattr(self._exporter, "shutdown"):
                # some exporters provide shutdown/force_flush style methods
                self._exporter.shutdown()
        except Exception:
            logger.exception("Failed to shutdown exporter")


def main():
    print(os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"))

    # exporter = ConsoleMetricExporter()
    exporter = AzureMonitorMetricExporter(
        connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    )
    # reader = MyPushReader(exporter)
    # reader = MetricReader(exporter)
    reader = PeriodicExportingMetricReader(exporter)
    provider = MeterProvider(metric_readers=[reader])
    metrics.set_meter_provider(provider)
    meter = metrics.get_meter(__name__)

    # Use a counter for manual updates (ObservableGauge caused compat issues)
    # counter = meter.create_counter(
    #     "queue_depth",
    #     unit="messages",
    #     description="Queue depth (manual)"
    # )
    gauge = meter.create_gauge(
        "queue_gauge_depth", unit="count", description="Count using gauge"
    )

    # reader.flush()

    # Add a sample value with attributes
    # counter.add(10, {"environment": "dev", "queue": "todo"})
    gauge.set(120, {"environment": "dev", "queue": "todo"})

    # Sleep a fraction to allow any internal scheduling (not required but nicer)
    time.sleep(0.1)

    # Force a flush (this will call reader._receive_metrics(timeout_millis=...))
    # try:
    #     provider.force_flush()
    #     logger.info("force_flush() completed without exception")
    # except Exception as exc:
    #     logger.exception("provider.force_flush() failed: %s", exc)

    # try:
    #     provider.shutdown()
    # except Exception:
    #     logger.exception("provider.shutdown() failed")


if __name__ == "__main__":
    main()
