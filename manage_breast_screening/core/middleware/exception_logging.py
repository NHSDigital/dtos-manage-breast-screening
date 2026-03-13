import logging
import re
import uuid
from contextvars import ContextVar

from django.utils.deprecation import MiddlewareMixin
from opentelemetry import trace as otel_trace

from manage_breast_screening.core.services.application_insights_logging import (
    ApplicationInsightsLogging,
)

# Attribute names set on the Django request object:
# Correlation ID for the request, included in log messages.
REQUEST_ATTR_CORRELATION_ID = "_correlation_id"
# Flag to indicate whether the exception has already been logged for this request, to prevent duplicate logging by django.request logger.
REQUEST_ATTR_EXCEPTION_LOGGED = "_exception_logged"
# Stores the ContextVar.Token returned by _correlation_id_ctx.set(), used to reset the context var and prevent leaking between requests.
REQUEST_ATTR_CORRELATION_ID_CTX_TOKEN = "_correlation_id_ctx_token"

_correlation_id_ctx = ContextVar(REQUEST_ATTR_CORRELATION_ID, default=None)


class ExceptionLoggingMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self._app_insights_logger = ApplicationInsightsLogging()

    def process_exception(self, request, exception):
        user = getattr(request, "user", None)
        user_repr = (
            str(user)
            if user and hasattr(user, "is_authenticated") and user.is_authenticated
            else "Anonymous"
        )

        correlation_id = getattr(request, REQUEST_ATTR_CORRELATION_ID, None)

        extra = {
            "url": request.path,
            "method": request.method,
            "user": user_repr,
            "correlation_id": correlation_id,
            "exception_type": type(exception).__name__,
        }
        extra_str = ", ".join(f"{k}={v}" for k, v in extra.items())
        self._app_insights_logger.exception(f"{extra_str} {exception}", extra=extra)

        setattr(request, REQUEST_ATTR_EXCEPTION_LOGGED, True)


class SuppressDuplicateExceptionFilter(logging.Filter):
    """
    Django's `django.request` logger logs every unhandled view exception at `ERROR` level
    automatically. `ExceptionLoggingMiddleware.process_exception` then logs the same exception
    again. Both reach Application Insights, creating duplicates in the `exceptions` / `traces`
    tables and inflating alert counts.

    This filter suppresses further logging if the exception has already been
    logged by ExceptionLoggingMiddleware.

    As SuppressDuplicateExceptionFilter relies on an attribute set by ExceptionLoggingMiddleware,
    if ExceptionLoggingMiddleware is not in MIDDLEWARE, the flag will never be set and duplicates will occur silently.
    """

    def filter(self, record):
        request = getattr(record, "request", None)

        if request and getattr(request, REQUEST_ATTR_EXCEPTION_LOGGED, False):
            return False

        return True


class CorrelationIdMiddleware(MiddlewareMixin):
    RESPONSE_HEADER = "X-Correlation-ID"
    CORRELATION_ID_HEADER = "HTTP_" + RESPONSE_HEADER.upper().replace("-", "_")
    # SAFE_ID_REGEX ensures that inbound correlation IDs are sanitized before use.
    # This prevents header injection and BadHeaderError by rejecting values with control characters or unsafe input.
    SAFE_ID_REGEX = re.compile(r"^[A-Za-z0-9._-]{1,64}$")

    def process_request(self, request):
        correlation_id = self.find_correlation_id(request)
        setattr(request, REQUEST_ATTR_CORRELATION_ID, correlation_id)

        # Store the previous token so can reset it later and prevent leaking between requests
        token = _correlation_id_ctx.set(correlation_id)
        setattr(request, REQUEST_ATTR_CORRELATION_ID_CTX_TOKEN, token)

    def find_correlation_id(self, request):
        """
        Use correlation ID from incoming request headers if exists and is safe, otherwise use OTel trace ID if available, otherwise generate a new UUID.
        """

        raw_id = request.META.get(self.CORRELATION_ID_HEADER)
        if raw_id and self.SAFE_ID_REGEX.match(raw_id):
            return raw_id

        span = otel_trace.get_current_span()
        ctx = span.get_span_context()
        if ctx.is_valid:
            # Use OTel trace ID - this links to all other App Insights telemetry
            return format(ctx.trace_id, "032x")

        return str(uuid.uuid4())

    def _reset_correlation_id_ctx(self, request):
        token = getattr(request, REQUEST_ATTR_CORRELATION_ID_CTX_TOKEN, None)
        if token is not None:
            _correlation_id_ctx.reset(token)
            setattr(request, REQUEST_ATTR_CORRELATION_ID_CTX_TOKEN, None)

    def process_response(self, request, response):
        correlation_id = getattr(request, REQUEST_ATTR_CORRELATION_ID, None)
        if correlation_id:
            response[self.RESPONSE_HEADER] = correlation_id
        self._reset_correlation_id_ctx(request)
        return response

    def process_exception(self, request, exception):
        self._reset_correlation_id_ctx(request)
        return None


class CorrelationIdFilter(logging.Filter):
    """
    This filter adds the correlation ID from the current request to log records, so it can be included log messages.

    If no correlation ID is set for the current request, it adds a placeholder value ("-") instead.

    Always returns True as is an enriching filter, not a suppressing one.
    """

    def filter(self, record):
        record.correlation_id = _correlation_id_ctx.get() or "-"
        return True
