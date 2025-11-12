import logging
import os

from azure.monitor.opentelemetry import configure_azure_monitor

from manage_breast_screening.config.settings import boolean_env


class ApplicationInsightsLogging:
    def __init__(self) -> None:
        self.logger_name = os.getenv(
            "APPLICATIONINSIGHTS_LOGGER_NAME", "manbrs-notifications"
        )
        self.logger = self.getLogger()

    def configure_azure_monitor(self):
        if boolean_env("APPLICATIONINSIGHTS_IS_ENABLED", False) and os.getenv(
            "APPLICATIONINSIGHTS_CONNECTION_STRING", ""
        ):
            # Configure OpenTelemetry to use Azure Monitor with the
            # APPLICATIONINSIGHTS_CONNECTION_STRING environment variable.
            configure_azure_monitor(
                # Set the namespace for the logger in which you would like to collect telemetry for if you are collecting logging telemetry. This is imperative so you do not collect logging telemetry from the SDK itself.
                logger_name=self.logger_name,
            )
        else:
            default_logger = logging.getLogger(__name__)
            default_logger.info("Application Insights logging not enabled")

    def getLogger(self):
        return logging.getLogger(self.logger_name)

    def exception(self, exception_name: str):
        self.logger.exception(exception_name, stack_info=True)

    def custom_event(self, message: str, event_name: str):
        self.logger.warning(
            message,
            extra={
                "microsoft.custom_event.name": event_name,
                "additional_attrs": message,
            },
        )
