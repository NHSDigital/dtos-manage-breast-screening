import logging
import os

from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.sdk.trace.sampling import ALWAYS_ON, ParentBased, TraceIdRatioBased
from opentelemetry.trace.span import TraceState
from opentelemetry.util.types import Attributes

from manage_breast_screening.config.settings.base import boolean_env


class _HealthCheckSampler(ParentBased):
    _healthcheck_sampler = TraceIdRatioBased(0.01)

    def should_sample(self, parent_context, trace_id, name, kind=None, attributes: Attributes = None, links=None, trace_state: TraceState = None):
        if attributes and str(attributes.get("http.target", "")).startswith("/healthcheck"):
            return self._healthcheck_sampler.should_sample(parent_context, trace_id, name, kind, attributes, links, trace_state)
        return super().should_sample(parent_context, trace_id, name, kind, attributes, links, trace_state)

    def __init__(self):
        super().__init__(root=ALWAYS_ON)


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
            configure_azure_monitor(sampler=_HealthCheckSampler())
            PsycopgInstrumentor().instrument(capture_parameters=True)
            # DjangoInstrumentor().instrument(exclude_urls=["/healthcheck"])
            DjangoInstrumentor().instrument()
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
