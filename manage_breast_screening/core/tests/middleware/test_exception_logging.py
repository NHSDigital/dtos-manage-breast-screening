import logging
import uuid
from unittest import mock

import pytest

from manage_breast_screening.core.middleware.exception_logging import (
    CorrelationIdFilter,
    CorrelationIdMiddleware,
    ExceptionLoggingMiddleware,
    SuppressDuplicateExceptionFilter,
    _correlation_id_ctx,
)


@pytest.fixture(autouse=True)
def reset_correlation_id_ctx():
    """Reset correlation_id_ctx to None after each test to prevent state leakage."""
    token = _correlation_id_ctx.set(None)
    yield
    _correlation_id_ctx.reset(token)


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
            self._correlation_id = correlation_id

    @pytest.fixture
    def middleware(self):
        return ExceptionLoggingMiddleware(lambda req: None)

    def test_process_exception_logs_with_authenticated_user(
        self, monkeypatch, middleware
    ):
        user = self.DummyUser(is_authenticated=True)
        request = self.DummyRequest(user=user, correlation_id="corr-id-123")
        exception = RuntimeError("Something went wrong")

        mock_logger = mock.Mock()
        middleware._app_insights_logger = mock_logger

        middleware.process_exception(request, exception)

        mock_logger.exception.assert_called_once_with(
            "url=/test/, method=GET, user=testuser, correlation_id=corr-id-123, exception_type=RuntimeError Something went wrong",
            extra={
                "url": "/test/",
                "method": "GET",
                "user": "testuser",
                "correlation_id": "corr-id-123",
                "exception_type": "RuntimeError",
            },
        )

    def test_process_exception_logs_with_anonymous_user(self, monkeypatch, middleware):
        user = self.DummyUser(is_authenticated=False)
        request = self.DummyRequest(user=user, correlation_id=None)
        exception = RuntimeError("Details of exception")

        mock_logger = mock.Mock()
        middleware._app_insights_logger = mock_logger

        middleware.process_exception(request, exception)

        mock_logger.exception.assert_called_once_with(
            "url=/test/, method=GET, user=Anonymous, correlation_id=None, exception_type=RuntimeError Details of exception",
            extra={
                "url": "/test/",
                "method": "GET",
                "user": "Anonymous",
                "correlation_id": None,
                "exception_type": "RuntimeError",
            },
        )

    def test_process_exception_logs_with_no_user(self, monkeypatch, middleware):
        request = self.DummyRequest(user=None, correlation_id="abc")
        exception = RuntimeError("Fail")

        mock_logger = mock.Mock()
        middleware._app_insights_logger = mock_logger

        middleware.process_exception(request, exception)

        mock_logger.exception.assert_called_once_with(
            "url=/test/, method=GET, user=Anonymous, correlation_id=abc, exception_type=RuntimeError Fail",
            extra={
                "url": "/test/",
                "method": "GET",
                "user": "Anonymous",
                "correlation_id": "abc",
                "exception_type": "RuntimeError",
            },
        )

    def test_process_exception_returns_none(self, middleware):
        request = self.DummyRequest()
        exception = RuntimeError("Some error")
        result = middleware.process_exception(request, exception)
        assert result is None

    def test_process_exception_does_not_mutate_correlation_id_ctx(
        self, monkeypatch, middleware
    ):
        _correlation_id_ctx.set("ctx-value")
        request = self.DummyRequest(correlation_id="request-corr-id")
        mock_logger = mock.Mock()
        middleware._app_insights_logger = mock_logger
        middleware.process_exception(request, RuntimeError("err"))
        assert _correlation_id_ctx.get() == "ctx-value"

    @pytest.mark.parametrize(
        "path,method",
        [
            ("/admin/", "POST"),
            ("/api/v1/resource/", "DELETE"),
            ("/", "PUT"),
        ],
    )
    def test_process_exception_logs_correct_path_and_method(
        self, monkeypatch, middleware, path, method
    ):
        user = self.DummyUser(is_authenticated=True)
        request = self.DummyRequest(
            path=path, method=method, user=user, correlation_id="x"
        )
        exception = RuntimeError("err")

        mock_logger = mock.Mock()
        middleware._app_insights_logger = mock_logger

        middleware.process_exception(request, exception)

        mock_logger.exception.assert_called_once_with(
            f"url={path}, method={method}, user=testuser, correlation_id=x, exception_type=RuntimeError err",
            extra={
                "url": path,
                "method": method,
                "user": "testuser",
                "correlation_id": "x",
                "exception_type": "RuntimeError",
            },
        )


class TestSuppressDuplicateExceptionFilter:
    @pytest.fixture
    def filter(self):
        return SuppressDuplicateExceptionFilter()

    def _make_record(self, request=None):
        record = logging.LogRecord(
            name="django.request",
            level=logging.ERROR,
            pathname="test_path",
            lineno=10,
            msg="Internal Server Error",
            args=(),
            exc_info=None,
        )
        if request is not None:
            record.request = request
        return record

    class DummyRequest:
        def __init__(self, exception_logged=None):
            if exception_logged is not None:
                self._exception_logged = exception_logged
            self.path = "/test/"
            self.method = "GET"

    def test_suppresses_when_exception_already_logged(self, filter):
        request = self.DummyRequest(exception_logged=True)
        record = self._make_record(request=request)
        assert filter.filter(record) is False

    def test_allows_when_exception_not_logged(self, filter):
        request = self.DummyRequest(exception_logged=False)
        record = self._make_record(request=request)
        assert filter.filter(record) is True

    def test_allows_when_request_has_no_exception_logged_attr(self, filter):
        request = self.DummyRequest()
        record = self._make_record(request=request)
        assert filter.filter(record) is True

    def test_allows_when_record_has_no_request_attr(self, filter):
        record = self._make_record()
        assert not hasattr(record, "request")
        assert filter.filter(record) is True

    def test_allows_when_request_is_none(self, filter):
        record = self._make_record()
        record.request = None
        assert filter.filter(record) is True

    def test_does_not_modify_request_exception_logged_flag(self, filter):
        request = self.DummyRequest(exception_logged=True)
        record = self._make_record(request=request)
        filter.filter(record)
        assert request._exception_logged is True

    def test_does_not_modify_record_when_suppressing(self, filter):
        request = self.DummyRequest(exception_logged=True)
        record = self._make_record(request=request)
        original_msg = record.msg
        filter.filter(record)
        assert record.msg == original_msg
        assert record.request is request

    def test_works_after_exception_logging_middleware_sets_flag(self, filter):
        request = self.DummyRequest()

        assert not hasattr(request, "_exception_logged")

        # ExceptionLoggingMiddleware.process_exception will set the flag on the request
        ExceptionLoggingMiddleware(lambda req: None).process_exception(
            request, RuntimeError("Test exception")
        )

        assert request._exception_logged is True

        record = self._make_record(request=request)

        # SuppressDuplicateExceptionFilter should now suppress this record since the flag is set
        assert filter.filter(record) is False


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
        assert request._correlation_id == "existing-id-123"
        assert _correlation_id_ctx.get() == "existing-id-123"

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
            assert request._correlation_id == "12345678-1234-5678-1234-567812345678"
            assert _correlation_id_ctx.get() == "12345678-1234-5678-1234-567812345678"

    def test_process_request_generates_new_correlation_id(self, middleware):
        with mock.patch(
            "uuid.uuid4", return_value=uuid.UUID("12345678-1234-5678-1234-567812345678")
        ):
            request = self.DummyRequest()
            middleware.process_request(request)
            assert request._correlation_id == "12345678-1234-5678-1234-567812345678"
            assert _correlation_id_ctx.get() == "12345678-1234-5678-1234-567812345678"

    def test_process_response_sets_header_when_correlation_id_present(self, middleware):
        request = self.DummyRequest()
        request._correlation_id = "test-corr-id"
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
        previous_value = "previous-correlation-id"
        _correlation_id_ctx.set(previous_value)

        request = self.DummyRequest()
        response = self.DummyResponse()

        middleware.process_request(request)
        new_value = request._correlation_id
        assert _correlation_id_ctx.get() == new_value
        assert request._correlation_id_ctx_token.old_value == previous_value

        middleware.process_response(request, response)
        assert _correlation_id_ctx.get() == previous_value
        assert not request._correlation_id_ctx_token

    def test_process_exception_resets_context(self, middleware):
        previous_value = "previous-correlation-id"
        _correlation_id_ctx.set(previous_value)

        request = self.DummyRequest()

        middleware.process_request(request)
        new_value = request._correlation_id
        assert _correlation_id_ctx.get() == new_value
        assert request._correlation_id_ctx_token.old_value == previous_value

        middleware.process_exception(request, RuntimeError("test"))
        assert _correlation_id_ctx.get() == previous_value
        assert not request._correlation_id_ctx_token

    def test_process_request_does_not_retain_previous_context_after_response(
        self, middleware
    ):
        """Context should be fully reset after process_response, not retain new correlation id."""
        request = self.DummyRequest(meta={"HTTP_X_CORRELATION_ID": "first-id"})
        response = self.DummyResponse()

        middleware.process_request(request)
        assert _correlation_id_ctx.get() == "first-id"

        middleware.process_response(request, response)
        assert _correlation_id_ctx.get() is None

    def test_process_request_stores_token_on_request(self, middleware):
        request = self.DummyRequest(meta={"HTTP_X_CORRELATION_ID": "some-id"})
        middleware.process_request(request)
        assert hasattr(request, "_correlation_id_ctx_token")
        assert request._correlation_id_ctx_token is not None

    def test_process_response_returns_response(self, middleware):
        request = self.DummyRequest()
        middleware.process_request(request)
        response = self.DummyResponse()
        result = middleware.process_response(request, response)
        assert result is response


class TestCorrelationIdFilter:
    @pytest.fixture
    def filter(self):
        return CorrelationIdFilter()

    def _make_record(self):
        return logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test_path",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

    def test_correlation_id_filter_uses_correlation_id_from_context(self, filter):
        test_correlation_id = "test-correlation-id-123"
        _correlation_id_ctx.set(test_correlation_id)

        record = self._make_record()

        assert filter.filter(record)
        assert record.correlation_id == test_correlation_id

    def test_correlation_id_filter_uses_default_when_not_set(self, filter):
        _correlation_id_ctx.set(None)

        record = self._make_record()

        assert filter.filter(record)
        assert record.correlation_id == "-"

    def test_correlation_id_filter_always_returns_true(self, filter):
        """Filter must always allow the record through."""
        _correlation_id_ctx.set(None)
        record = self._make_record()
        assert filter.filter(record) is True

    def test_correlation_id_filter_does_not_mutate_context(self, filter):
        """Filtering a record must not change the context var."""
        _correlation_id_ctx.set("stable-id")
        record = self._make_record()
        filter.filter(record)
        assert _correlation_id_ctx.get() == "stable-id"
