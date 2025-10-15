import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages import INFO, SUCCESS
from django.contrib.messages.storage.base import Message
from django.test import RequestFactory
from django.utils.safestring import mark_safe
from markupsafe import Markup
from pytest_django.asserts import assertHTMLEqual

from manage_breast_screening.auth.tests.factories import UserFactory
from manage_breast_screening.clinics.tests.factories import UserAssignmentFactory
from manage_breast_screening.core.template_helpers import (
    header_account_items,
    info_banner,
    message_with_heading,
    success_banner,
)


@pytest.mark.django_db
class TestHeaderAccountItems:
    def test_user_with_no_role(self):
        user = UserFactory.create(first_name="Firstname", last_name="Lastname")
        assert header_account_items(user) == [
            {"text": "LASTNAME, Firstname", "icon": True},
            {"href": "/auth/log-out/", "text": "Log out"},
        ]

    def test_user_with_role(self):
        user = UserFactory.create(first_name="Firstname", last_name="Lastname")
        UserAssignmentFactory.create(clinical=True, user=user)
        assert header_account_items(user) == [
            {"text": "LASTNAME, Firstname (Clinical)", "icon": True},
            {"href": "/auth/log-out/", "text": "Log out"},
        ]

    def test_anonymous_user(self):
        user = AnonymousUser()
        assert header_account_items(user) == [
            {"href": "/auth/log-in/", "text": "Log in"},
        ]


class TestMessageWithHeading:
    def test_message_with_heading(self):
        result = message_with_heading("Heading", Markup("<p>Content</p>"))

        assertHTMLEqual(
            result,
            """
            <h3 class="nhsuk-notification-banner__heading">Heading</h3>
            <p>Content</p>
            """,
        )

    def test_message_with_heading_and_unsafe_content(self):
        result = message_with_heading(
            "Created widget", "Created <script>alert(1)</script>"
        )

        assertHTMLEqual(
            result,
            """
            <h3 class="nhsuk-notification-banner__heading">Created widget</h3>
            Created &lt;script&gt;alert(1)&lt;/script&gt;
            """,
        )


class TestNotificationBannerParamsForStringMessages:
    @pytest.fixture
    def dummy_request(self):
        request = RequestFactory().get("/")
        request._messages = [
            Message(message="abc", level=INFO),
            Message(message="def", level=SUCCESS),
        ]
        return request

    def test_info_banner_with_text_message(self, dummy_request):
        result = info_banner(dummy_request)
        assert result == {"text": "abc"}

    def test_success_banner_with_text_message(self, dummy_request):
        result = success_banner(dummy_request)
        assert result == {"text": "def", "type": "success"}


class TestNotificationBannerParamsForHTMLMessages:
    @pytest.fixture
    def dummy_request(self):
        request = RequestFactory().get("/")
        request._messages = [
            Message(message=mark_safe("abc"), level=INFO),
            Message(message=mark_safe("def"), level=SUCCESS),
        ]
        return request

    def test_info_banner_with_html_message(self, dummy_request):
        result = info_banner(dummy_request)
        assert result == {"html": mark_safe("abc")}

    def test_success_banner_with_html_message(self, dummy_request):
        result = success_banner(dummy_request)
        assert result == {"html": mark_safe("def"), "type": "success"}
