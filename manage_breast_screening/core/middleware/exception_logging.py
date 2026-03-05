import logging
import re
import uuid
from contextvars import ContextVar

from django.utils.deprecation import MiddlewareMixin

from manage_breast_screening.core.services.application_insights_logging import (
    ApplicationInsightsLogging,
)

app_insights_logger = ApplicationInsightsLogging()
correlation_id_ctx = ContextVar("correlation_id", default=None)


class ExceptionLoggingMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        user = getattr(request, "user", None)
        user_repr = (
            str(user)
            if user and hasattr(user, "is_authenticated") and user.is_authenticated
            else "Anonymous"
        )
        context = (
            f"URL: {request.path}, "
            f"Method: {request.method}, "
            f"User: {user_repr}, "
            f"Exception: {exception}"
        )
        correlation_id = getattr(request, "correlation_id", None)
        app_insights_logger.exception(context, correlation_id=correlation_id)

        return None


class CorrelationIdMiddleware(MiddlewareMixin):
    RESPONSE_HEADER = "X-Correlation-ID"
    CORRELATION_ID_HEADER = "HTTP_" + RESPONSE_HEADER.upper().replace("-", "_")
    # SAFE_ID_REGEX ensures that inbound correlation IDs are sanitized before use.
    # This prevents header injection and BadHeaderError by rejecting values with control characters or unsafe input.
    SAFE_ID_REGEX = re.compile(r"^[A-Za-z0-9._-]{1,64}$")

    def process_request(self, request):
        raw_id = request.META.get(self.CORRELATION_ID_HEADER)
        if raw_id and self.SAFE_ID_REGEX.match(raw_id):
            correlation_id = raw_id
        else:
            correlation_id = str(uuid.uuid4())
        request.correlation_id = correlation_id

        # Store the token so we can reset later
        request._correlation_id_token = correlation_id_ctx.set(correlation_id)

    def process_response(self, request, response):
        correlation_id = getattr(request, "correlation_id", None)
        if correlation_id:
            response["X-Correlation-ID"] = correlation_id
        # Reset the context var to avoid leaking
        token = getattr(request, "_correlation_id_token", None)
        if token is not None:
            correlation_id_ctx.reset(token)
            request._correlation_id_token = None
        return response

    def process_exception(self, request, exception):
        # Reset the context var to avoid leaking
        token = getattr(request, "_correlation_id_token", None)
        if token is not None:
            correlation_id_ctx.reset(token)
            request._correlation_id_token = None
        return None


class CorrelationIdFilter(logging.Filter):
    """
    Logging filter that injects the current correlation ID into each log record.

    Ensures that all logs generated for a request are tagged with the same correlation ID.
    If a correlation_id is explicitly provided via extra={...} then is preserved and takes precedence over the context var.
    If no correlation ID is provided via extra={...} nor set in the context, a default value of "-" is used.
    """

    def filter(self, record):
        existing_correlation_id = getattr(record, "correlation_id", None)
        if existing_correlation_id is None:
            record.correlation_id = correlation_id_ctx.get() or "-"
        return True
