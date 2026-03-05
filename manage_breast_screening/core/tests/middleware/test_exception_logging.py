import logging
import uuid
from unittest import mock

import pytest

from manage_breast_screening.core.middleware.exception_logging import (
    CorrelationIdFilter,
    CorrelationIdMiddleware,
    ExceptionLoggingMiddleware,
    correlation_id_ctx,
)


class TestExceptionLoggingMiddleware:
    class DummyUser:
        def __init__(self, is_authenticated=True):
            self.is_authenticated = is_authenticated

        def __str__(self):
            return "testuser"

    class DummyRequest:
        def __init__(self, path="/test/", method="GET", user=None, correlation_id=None):
            self.path = path
            self.method = method
            self.user = user
            self.correlation_id = correlation_id

    @pytest.fixture
    def middleware(self):
        return ExceptionLoggingMiddleware(lambda req: None)

    def test_process_exception_logs_with_authenticated_user(
        self, monkeypatch, middleware
    ):
        user = self.DummyUser(is_authenticated=True)
        request = self.DummyRequest(user=user, correlation_id="corr-id-123")
        exception = Exception("Something went wrong")

        mock_logger = mock.Mock()
        monkeypatch.setattr(
            "manage_breast_screening.core.middleware.exception_logging.app_insights_logger",
            mock_logger,
        )

        middleware.process_exception(request, exception)

        expected_context = (
            "URL: /test/, Method: GET, User: testuser, Exception: Something went wrong"
        )
        mock_logger.exception.assert_called_once_with(
            expected_context, correlation_id="corr-id-123"
        )

    def test_process_exception_logs_with_anonymous_user(self, monkeypatch, middleware):
        user = self.DummyUser(is_authenticated=False)
        request = self.DummyRequest(user=user, correlation_id=None)
        exception = Exception("Oops")

        mock_logger = mock.Mock()
        monkeypatch.setattr(
            "manage_breast_screening.core.middleware.exception_logging.app_insights_logger",
            mock_logger,
        )

        middleware.process_exception(request, exception)

        expected_context = "URL: /test/, Method: GET, User: Anonymous, Exception: Oops"
        mock_logger.exception.assert_called_once_with(
            expected_context, correlation_id=None
        )

    def test_process_exception_logs_with_no_user(self, monkeypatch, middleware):
        request = self.DummyRequest(user=None, correlation_id="abc")
        exception = Exception("Fail")

        mock_logger = mock.Mock()
        monkeypatch.setattr(
            "manage_breast_screening.core.middleware.exception_logging.app_insights_logger",
            mock_logger,
        )

        middleware.process_exception(request, exception)

        expected_context = "URL: /test/, Method: GET, User: Anonymous, Exception: Fail"
        mock_logger.exception.assert_called_once_with(
            expected_context, correlation_id="abc"
        )


class TestCorrelationIdMiddleware:
    class DummyRequest:
        def __init__(self, meta=None):
            self.META = meta or {}
            self.correlation_id = None

    class DummyResponse(dict):
        pass

    @pytest.fixture
    def middleware(self):
        return CorrelationIdMiddleware(lambda req: None)

    def test_process_request_uses_existing_correlation_id(self, middleware):
        request = self.DummyRequest(meta={"HTTP_X_CORRELATION_ID": "existing-id-123"})
        middleware.process_request(request)
        assert request.correlation_id == "existing-id-123"
        assert correlation_id_ctx.get() == "existing-id-123"

    @pytest.mark.parametrize(
        "invalid_id",
        [
            "invalid_id!",
            "id with spaces",
            "id_with_@_symbol",
            "a" * 65,  # Exceeds max length of 64
            "id\nwithnewline",
            "",
        ],
    )
    def test_process_request_ignores_invalid_correlation_id(
        self, middleware, invalid_id
    ):
        with mock.patch(
            "uuid.uuid4", return_value=uuid.UUID("12345678-1234-5678-1234-567812345678")
        ):
            request = self.DummyRequest(meta={"HTTP_X_CORRELATION_ID": invalid_id})
            middleware.process_request(request)
            assert request.correlation_id == "12345678-1234-5678-1234-567812345678"
            assert correlation_id_ctx.get() == "12345678-1234-5678-1234-567812345678"

    def test_process_request_generates_new_correlation_id(self, middleware):
        with mock.patch(
            "uuid.uuid4", return_value=uuid.UUID("12345678-1234-5678-1234-567812345678")
        ):
            request = self.DummyRequest()
            middleware.process_request(request)
            assert request.correlation_id == "12345678-1234-5678-1234-567812345678"
            assert correlation_id_ctx.get() == "12345678-1234-5678-1234-567812345678"

    def test_process_response_sets_header_when_correlation_id_present(self, middleware):
        request = self.DummyRequest()
        request.correlation_id = "test-corr-id"
        response = self.DummyResponse()
        result = middleware.process_response(request, response)
        assert result["X-Correlation-ID"] == "test-corr-id"

    def test_process_response_does_not_set_header_when_correlation_id_missing(
        self, middleware
    ):
        request = self.DummyRequest()
        response = self.DummyResponse()
        result = middleware.process_response(request, response)
        assert "X-Correlation-ID" not in result

    def test_process_response_resets_context(self, middleware):
        # Set up a previous value in the context
        previous_value = "previous-correlation-id"
        correlation_id_ctx.set(previous_value)

        request = self.DummyRequest()
        response = self.DummyResponse()

        # process_request sets a new correlation_id and stores its token
        middleware.process_request(request)
        new_value = request.correlation_id
        assert correlation_id_ctx.get() == new_value
        assert request._correlation_id_token.old_value == previous_value

        # process_response should reset to previous_value
        middleware.process_response(request, response)
        assert correlation_id_ctx.get() == previous_value
        assert not request._correlation_id_token

    def test_process_exception_resets_context(self, middleware):
        # Set up a previous value in the context
        previous_value = "previous-correlation-id"
        correlation_id_ctx.set(previous_value)

        request = self.DummyRequest()
        response = self.DummyResponse()

        # process_request sets a new correlation_id and stores its token
        middleware.process_request(request)
        new_value = request.correlation_id
        assert correlation_id_ctx.get() == new_value
        assert request._correlation_id_token.old_value == previous_value

        # process_exception should reset to previous_value
        middleware.process_exception(request, response)
        assert correlation_id_ctx.get() == previous_value
        assert not request._correlation_id_token


class TestCorrelationIdFilter:
    @pytest.fixture
    def filter(self):
        return CorrelationIdFilter()

    def test_correlation_id_filter_uses_correlation_id_from_context(self, filter):
        # Set a correlation ID in the context
        test_correlation_id = "test-correlation-id-123"
        correlation_id_ctx.set(test_correlation_id)

        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test_path",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        assert filter.filter(record)
        assert record.correlation_id == test_correlation_id

    def test_correlation_id_filter_preserves_existing_correlation_id(self, filter):
        # Set a correlation ID in the context. This should be ignored in favour of the correlation_id already present in the record.
        correlation_id_ctx.set("context-correlation-id-123")

        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test_path",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.correlation_id = "record-correlation-id-123"

        assert filter.filter(record)
        assert record.correlation_id == "record-correlation-id-123"

    def test_correlation_id_filter_uses_default_when_not_set(self, filter):
        # Clear the context variable
        correlation_id_ctx.set(None)

        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test_path",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        assert filter.filter(record)
        assert record.correlation_id == "-"
