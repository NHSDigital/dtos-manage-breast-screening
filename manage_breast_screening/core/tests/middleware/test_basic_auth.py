import base64
from typing import Callable

import pytest
from django.http import HttpResponse
from django.test import RequestFactory

from manage_breast_screening.core.decorators import basic_auth_exempt
from manage_breast_screening.core.middleware.basic_auth import BasicAuthMiddleware


def _make_middleware(get_response: Callable | None = None) -> BasicAuthMiddleware:
    return BasicAuthMiddleware(get_response or (lambda r: HttpResponse("OK")))


def _auth_header(username: str, password: str) -> str:
    token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")
    return f"Basic {token}"


@pytest.mark.django_db
class TestBasicAuthMiddleware:
    def test_disabled_auth_allows_request(self, settings):
        settings.BASIC_AUTH_ENABLED = False
        request = RequestFactory().get("/")

        mw = _make_middleware()
        # With auth disabled, middleware should not block
        assert mw.process_view(request, lambda r: None, (), {}) is None

    def test_exempt_view_allows_request(self, settings):
        settings.BASIC_AUTH_ENABLED = True
        request = RequestFactory().get("/")

        def view(_request):
            return HttpResponse("OK")

        # Mark view as exempt using the decorator
        basic_auth_exempt(view)

        mw = _make_middleware()
        assert mw.process_view(request, view, (), {}) is None

    def test_debug_toolbar_allows_request(self, settings):
        settings.BASIC_AUTH_ENABLED = True
        settings.DEBUG_TOOLBAR = True

        request = RequestFactory().get("/__debug__/panel")
        mw = _make_middleware()
        assert mw.process_view(request, lambda r: None, (), {}) is None

    def test_missing_header_unauthorized(self, settings):
        settings.BASIC_AUTH_ENABLED = True
        settings.BASIC_AUTH_USERNAME = "user"
        settings.BASIC_AUTH_PASSWORD = "pass"
        settings.BASIC_AUTH_REALM = "Restricted Area"

        request = RequestFactory().get("/")
        mw = _make_middleware()
        resp = mw.process_view(request, lambda r: None, (), {})
        assert resp is not None
        assert resp.status_code == 401
        assert resp["WWW-Authenticate"] == 'Basic realm="Restricted Area"'

    def test_wrong_credentials_unauthorized(self, settings):
        settings.BASIC_AUTH_ENABLED = True
        settings.BASIC_AUTH_USERNAME = "user"
        settings.BASIC_AUTH_PASSWORD = "pass"

        request = RequestFactory().get(
            "/", HTTP_AUTHORIZATION=_auth_header("bad", "creds")
        )
        mw = _make_middleware()
        resp = mw.process_view(request, lambda r: None, (), {})
        assert resp is not None
        assert resp.status_code == 401
        assert resp["WWW-Authenticate"].startswith("Basic realm=")

    def test_correct_credentials_allows_request(self, settings):
        settings.BASIC_AUTH_ENABLED = True
        settings.BASIC_AUTH_USERNAME = "user"
        settings.BASIC_AUTH_PASSWORD = "pass"

        request = RequestFactory().get(
            "/", HTTP_AUTHORIZATION=_auth_header("user", "pass")
        )
        mw = _make_middleware()
        assert mw.process_view(request, lambda r: None, (), {}) is None

    def test_empty_credentials_unauthorized(self, settings):
        settings.BASIC_AUTH_ENABLED = True
        settings.BASIC_AUTH_USERNAME = ""
        settings.BASIC_AUTH_PASSWORD = ""

        request = RequestFactory().get("/", HTTP_AUTHORIZATION=_auth_header("", ""))
        mw = _make_middleware()
        resp = mw.process_view(request, lambda r: None, (), {})
        assert resp is not None
        assert resp.status_code == 401

    def test_api_path_allows_request(self, settings):
        settings.BASIC_AUTH_ENABLED = True

        request = RequestFactory().get("/api/v1/resource")
        mw = _make_middleware()
        # API paths should bypass basic auth
        assert mw.process_view(request, lambda r: None, (), {}) is None
