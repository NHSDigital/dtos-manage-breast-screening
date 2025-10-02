import logging
import os

from azure.monitor.opentelemetry import configure_azure_monitor


class ApplicationInsightsLogging:
    def __init__(self) -> None:
        self.logger = self.getLogger()

    @staticmethod
    def getLogger():
        try:
            logger_name = os.getenv(
                "APPLICATIONINSIGHTS_LOGGER_NAME", "manbrs-notifications-local"
            )
            # Configure OpenTelemetry to use Azure Monitor with the
            # APPLICATIONINSIGHTS_CONNECTION_STRING environment variable.
            configure_azure_monitor(
                # Set the namespace for the logger in which you would like to collect telemetry for if you are collecting logging telemetry. This is imperative so you do not collect logging telemetry from the SDK itself.
                logger_name=logger_name,
            )
            # Logging telemetry will be collected from logging calls made with this logger and all of it's children loggers.
            return logging.getLogger(logger_name)
        except Exception as e:
            # if insights isn't configured
            default_logger = logging.getLogger(__name__)
            default_logger.info("Failed to configure Application Insights %s", e)
            return default_logger

    def raise_an_exception(self, exception_name: str):
        self.logger.exception(exception_name, stack_info=True)

    def trigger_an_event(self, event_name: str, additional_attrs: str):
        self.logger.warning(
            event_name,
            extra={
                "microsoft.custom_event.name": event_name,
                "additional_attrs": additional_attrs,
            },
        )
