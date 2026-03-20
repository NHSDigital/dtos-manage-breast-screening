from typing import Callable

import pytest
from django.http import HttpResponse
from django.test import RequestFactory

from manage_breast_screening.core.decorators import service_enabled_exempt
from manage_breast_screening.core.middleware.service_enabled import (
    ServiceEnabledMiddleware,
)


def _make_middleware(get_response: Callable | None = None) -> ServiceEnabledMiddleware:
    return ServiceEnabledMiddleware(get_response or (lambda r: HttpResponse("OK")))


@pytest.mark.django_db
class TestServiceEnabledMiddleware:
    def test_service_enabled_allows_request(self, settings):
        settings.SERVICE_ENABLED = True
        request = RequestFactory().get("/")

        mw = _make_middleware()
        assert mw.process_view(request, lambda r: None, (), {}) is None

    def test_service_disabled_returns_503(self, settings):
        settings.SERVICE_ENABLED = False
        request = RequestFactory().get("/")

        mw = _make_middleware()
        resp = mw.process_view(request, lambda r: None, (), {})
        assert resp is not None
        assert resp.status_code == 503
        assert b"Sorry, this service is unavailable" in resp.content

    def test_service_disabled_exempt_view_allows_request(self, settings):
        settings.SERVICE_ENABLED = False
        request = RequestFactory().get("/healthcheck")

        def view(_request):
            return HttpResponse("OK")

        service_enabled_exempt(view)

        mw = _make_middleware()
        assert mw.process_view(request, view, (), {}) is None

    def test_missing_setting_defaults_to_enabled(self, settings):
        del settings.SERVICE_ENABLED
        request = RequestFactory().get("/")

        mw = _make_middleware()
        assert mw.process_view(request, lambda r: None, (), {}) is None
