from unittest.mock import patch

from django.test import RequestFactory

from manage_breast_screening.core.middleware.auth import (
    ManageAuthenticationMiddleware,
    ManageLoginRequiredMiddleware,
)


def test_authentication_middleware_skips_api_path():
    request = RequestFactory().get("/api/test/")
    middleware = ManageAuthenticationMiddleware(lambda r: None)

    with patch(
        "django.contrib.auth.middleware.AuthenticationMiddleware.process_request"
    ) as mocked_process_request:
        middleware.process_request(request)

    mocked_process_request.assert_not_called()


def test_authentication_middleware_calls_parent_for_non_api_path():
    request = RequestFactory().get("/not-the-api/")
    middleware = ManageAuthenticationMiddleware(lambda r: None)

    with patch(
        "django.contrib.auth.middleware.AuthenticationMiddleware.process_request"
    ) as mocked_process_request:
        middleware.process_request(request)

    mocked_process_request.assert_called_once_with(request)


def test_login_required_middleware_allows_api_path():
    request = RequestFactory().get("/api/test/")
    middleware = ManageLoginRequiredMiddleware(lambda r: None)

    response = middleware.process_view(
        request,
        view_func=lambda r: None,
        view_args=[],
        view_kwargs={},
    )

    assert response is None


def test_login_required_middleware_calls_parent_for_non_api_path():
    request = RequestFactory().get("/dashboard/")
    middleware = ManageLoginRequiredMiddleware(lambda r: None)

    with patch(
        "django.contrib.auth.middleware.LoginRequiredMiddleware.process_view"
    ) as mocked_process_view:
        middleware.process_view(
            request,
            view_func=lambda r: None,
            view_args=[],
            view_kwargs={},
        )

    mocked_process_view.assert_called_once()
