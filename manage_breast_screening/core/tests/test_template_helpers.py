import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages import ERROR, INFO, SUCCESS, WARNING
from django.contrib.messages.storage.base import Message
from django.test import RequestFactory
from django.utils.safestring import mark_safe
from markupsafe import Markup
from pytest_django.asserts import assertHTMLEqual

from manage_breast_screening.clinics.tests.factories import UserAssignmentFactory
from manage_breast_screening.core.template_helpers import (
    get_notification_banner_params,
    header_account_items,
    message_with_heading,
)
from manage_breast_screening.users.tests.factories import UserFactory


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
            Message(message="warning!", level=WARNING),
            Message(message="error!!!", level=ERROR),
        ]
        return request

    def test_info_banner_with_text_message(self, dummy_request):
        result = get_notification_banner_params(dummy_request, "info")
        assert result == {"text": "abc", "type": "info", "disableAutoFocus": True}

    def test_success_banner_with_text_message(self, dummy_request):
        result = get_notification_banner_params(dummy_request, "success")
        assert result == {"text": "def", "type": "success", "disableAutoFocus": True}

    def test_warning_banner_with_text_message(self, dummy_request):
        result = get_notification_banner_params(dummy_request, "warning")
        assert result == {
            "text": "warning!",
            "type": "warning",
            "disableAutoFocus": True,
        }

    def test_invalid_message_type(self, dummy_request):
        with pytest.raises(
            ValueError,
            match="message_type must be one of {info, warning, success}; got error",
        ):
            get_notification_banner_params(dummy_request, "error")

    def test_autofocus_param(self, dummy_request):
        result = get_notification_banner_params(
            dummy_request, "info", disable_auto_focus=False
        )
        assert result == {"text": "abc", "type": "info", "disableAutoFocus": False}


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
        result = get_notification_banner_params(dummy_request, "info")
        assert result == {
            "html": mark_safe("abc"),
            "type": "info",
            "disableAutoFocus": True,
        }

    def test_success_banner_with_html_message(self, dummy_request):
        result = get_notification_banner_params(dummy_request, "success")
        assert result == {
            "html": mark_safe("def"),
            "type": "success",
            "disableAutoFocus": True,
        }
