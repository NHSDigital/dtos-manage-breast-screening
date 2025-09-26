from typing import Callable
from unittest.mock import Mock

import pytest
from django.http import HttpResponse
from django.test import RequestFactory

from manage_breast_screening.core.decorators import current_provider_exempt
from manage_breast_screening.core.middleware.current_provider import (
    CurrentProviderMiddleware,
)


def _make_middleware(get_response: Callable | None = None) -> CurrentProviderMiddleware:
    return CurrentProviderMiddleware(get_response or (lambda r: HttpResponse("OK")))


@pytest.mark.django_db
class TestCurrentProviderMiddleware:
    def test_unauthenticated_user_allows_request(self):
        request = RequestFactory().get("/")
        request.user = Mock(is_authenticated=False)
        request.session = {}

        mw = _make_middleware()
        assert mw.process_view(request, lambda r: None, (), {}) is None

    def test_authenticated_user_with_current_provider_allows_request(self):
        request = RequestFactory().get("/")
        request.user = Mock(is_authenticated=True)
        request.session = {"current_provider": "123"}

        mw = _make_middleware()
        assert mw.process_view(request, lambda r: None, (), {}) is None

    def test_exempt_view_allows_request(self):
        request = RequestFactory().get("/")
        request.user = Mock(is_authenticated=True)
        request.session = {}

        def view(_request):
            return HttpResponse("OK")

        # Mark view as exempt using the decorator
        current_provider_exempt(view)

        mw = _make_middleware()
        assert mw.process_view(request, view, (), {}) is None

    def test_authenticated_user_without_current_provider_redirects(self):
        request = RequestFactory().get("/")
        request.user = Mock(is_authenticated=True)
        request.session = {}

        mw = _make_middleware()
        response = mw.process_view(request, lambda r: None, (), {})

        assert response is not None
        assert response.status_code == 302
        assert response.url == "/clinics/select-provider/"
