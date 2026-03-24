import logging
import os

from azure.monitor.opentelemetry import configure_azure_monitor

from manage_breast_screening.config.settings.base import boolean_env


class ApplicationInsightsLogging:
    def __init__(self) -> None:
        self.logger_name = os.getenv(
            "APPLICATIONINSIGHTS_LOGGER_NAME", "insights-logger"
        )
        os.environ.setdefault("OTEL_SERVICE_NAME", "manage-breast-screening")
        self.logger = self.getLogger()

    def configure_azure_monitor(self):
        if boolean_env("APPLICATIONINSIGHTS_IS_ENABLED", False) and os.getenv(
            "APPLICATIONINSIGHTS_CONNECTION_STRING", ""
        ):
            # Configure OpenTelemetry to use Azure Monitor with the
            # APPLICATIONINSIGHTS_CONNECTION_STRING environment variable.
            configure_azure_monitor()
        else:
            default_logger = logging.getLogger(__name__)
            default_logger.info("Application Insights logging not enabled")

    def getLogger(self):
        return logging.getLogger(self.logger_name)

    def exception(self, message: str, extra: dict = None):
        # Keys in extra are forwarded to Application Insights
        # as customDimensions and become filterable in the Logs blade and alerting rules.
        self.logger.exception(message, extra=extra)

    def custom_event_info(self, message: str, event_name: str):
        self.logger.info(
            message,
            extra={
                "microsoft.custom_event.name": event_name,
                "additional_attrs": message,
            },
        )
