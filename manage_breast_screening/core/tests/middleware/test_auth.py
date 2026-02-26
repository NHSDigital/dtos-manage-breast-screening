from unittest.mock import patch

from django.conf import settings
from django.test import RequestFactory
from django.urls import reverse

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


def test_manage_authentication_in_middleware():
    assert (
        "manage_breast_screening.core.middleware.auth.ManageAuthenticationMiddleware"
        in settings.MIDDLEWARE
    )
    assert (
        "manage_breast_screening.core.middleware.auth.ManageLoginRequiredMiddleware"
        in settings.MIDDLEWARE
    )


def test_unauthenticated_redirects_to_login(client):
    url = reverse("clinics:index")
    response = client.get(url)
    assert response.status_code == 302
    assert response.url == reverse(settings.LOGIN_URL) + "?next=" + url
