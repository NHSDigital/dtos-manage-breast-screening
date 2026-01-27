from datetime import timedelta
from unittest.mock import Mock, patch

import pytest
from django.http import HttpResponse
from django.test import RequestFactory
from django.utils import timezone

from manage_breast_screening.core.middleware.session_timeout import (
    SessionTimeoutMiddleware,
)
from manage_breast_screening.users.tests.factories import UserFactory

MODULE_PATH = "manage_breast_screening.core.middleware.session_timeout"


class MockSession(dict):
    """A dict subclass that mimics Django's session with a modified attribute."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.modified = False


@pytest.fixture
def middleware():
    return SessionTimeoutMiddleware(lambda _r: HttpResponse("OK"))


@pytest.fixture
def mock_logout():
    with patch(f"{MODULE_PATH}.auth_logout") as mock:
        yield mock


@pytest.fixture
def frozen_now():
    with patch(f"{MODULE_PATH}.timezone") as mock_tz:
        now = timezone.now()
        mock_tz.now.return_value = now
        yield now


@pytest.fixture
def user():
    return UserFactory()


def make_authenticated_request(user):
    request = RequestFactory().get("/")
    request.user = user
    request.session = MockSession()
    return request


@pytest.mark.django_db
class TestSessionTimeoutMiddleware:
    def test_unauthenticated_request_passes_through(self, middleware):
        request = RequestFactory().get("/")
        request.user = Mock(is_authenticated=False)
        request.session = {}

        response = middleware(request)

        assert response.status_code == 200

    def test_authenticated_request_initializes_last_activity(
        self, user, middleware, frozen_now
    ):
        request = make_authenticated_request(user)
        request.session["login_time"] = frozen_now.isoformat()

        response = middleware(request)

        assert response.status_code == 200
        assert request.session["last_activity"] == frozen_now.isoformat()
        assert request.session.modified

    def test_inactivity_timeout_logs_out_after_15_minutes(
        self, user, middleware, mock_logout, frozen_now
    ):
        request = make_authenticated_request(user)
        past = frozen_now - timedelta(minutes=16)
        request.session["login_time"] = past.isoformat()
        request.session["last_activity"] = past.isoformat()

        response = middleware(request)

        mock_logout.assert_called_once_with(request)
        assert response.status_code == 302

    def test_activity_within_timeout_does_not_logout(
        self, user, middleware, frozen_now
    ):
        request = make_authenticated_request(user)
        recent = frozen_now - timedelta(minutes=5)
        request.session["login_time"] = recent.isoformat()
        request.session["last_activity"] = recent.isoformat()

        response = middleware(request)

        assert response.status_code == 200

    def test_hard_timeout_logs_out_after_12_hours(
        self, user, middleware, mock_logout, frozen_now
    ):
        request = make_authenticated_request(user)
        login_time = frozen_now - timedelta(hours=13)
        request.session["login_time"] = login_time.isoformat()
        request.session["last_activity"] = frozen_now.isoformat()

        response = middleware(request)

        mock_logout.assert_called_once_with(request)
        assert response.status_code == 302

    def test_activity_threshold_prevents_frequent_db_writes(
        self, user, middleware, frozen_now
    ):
        request = make_authenticated_request(user)
        recent_activity = frozen_now - timedelta(seconds=30)
        request.session["login_time"] = recent_activity.isoformat()
        request.session["last_activity"] = recent_activity.isoformat()

        middleware(request)

        assert request.session["last_activity"] == recent_activity.isoformat()
        assert request.session.modified is False

    def test_activity_threshold_updates_after_60_seconds(
        self, user, middleware, frozen_now
    ):
        request = make_authenticated_request(user)
        old_activity = frozen_now - timedelta(seconds=61)
        request.session["login_time"] = old_activity.isoformat()
        request.session["last_activity"] = old_activity.isoformat()

        middleware(request)

        assert request.session["last_activity"] == frozen_now.isoformat()
        assert request.session.modified is True

    def test_missing_login_time_forces_logout(self, user, middleware, mock_logout):
        request = make_authenticated_request(user)
        request.session["last_activity"] = timezone.now().isoformat()

        response = middleware(request)

        mock_logout.assert_called_once_with(request)
        assert response.status_code == 302

    def test_api_path_bypasses_middleware(self, middleware):
        request = RequestFactory().get("/api/some-endpoint/")

        response = middleware(request)

        assert response.status_code == 200
