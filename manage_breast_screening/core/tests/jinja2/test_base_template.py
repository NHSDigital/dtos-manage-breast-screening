from unittest.mock import MagicMock

import pytest
from django.contrib.messages import SUCCESS
from django.contrib.messages.storage.base import Message
from django.forms import Form
from django.test import RequestFactory
from django.utils.safestring import mark_safe
from pytest_django.asserts import assertInHTML

form = MagicMock(autospec=Form)
form.errors = {}
form_with_errors = MagicMock(autospec=Form)
form_with_errors.errors = {"field": ["mooo"]}


@pytest.mark.parametrize(
    "page_title,form,expected_title",
    [
        ("", None, "Manage breast screening – NHS"),
        ("Page 1", None, "Page 1 – Manage breast screening – NHS"),
        ("Page 2", form_with_errors, "Error: Page 2 – Manage breast screening – NHS"),
        ("Page 3", form, "Page 3 – Manage breast screening – NHS"),
    ],
)
def test_page_title(jinja_env, page_title, form, expected_title):
    template = jinja_env.from_string(
        """
    {% extends "layout-app.jinja" %}
    """
    )
    html = template.render({"page_title": page_title, "form": form})
    assert f"<title>{expected_title}</title>" in html


def test_success_banner(jinja_env):
    template = jinja_env.from_string(
        """
        {% extends "layout-app.jinja" %}
        """
    )
    request = RequestFactory().get("/")
    request._messages = [Message(level=SUCCESS, message="Did a thing")]

    html = template.render(
        {
            "request": request,
        }
    )

    assertInHTML(
        """
        <div class="nhsuk-notification-banner nhsuk-notification-banner--success" role="alert" aria-labelledby="nhsuk-notification-banner-title" data-module="nhsuk-notification-banner" data-disable-auto-focus="true">
            <div class="nhsuk-notification-banner__header">
                <h2 class="nhsuk-notification-banner__title" id="nhsuk-notification-banner-title">Success</h2>
            </div>
            <div class="nhsuk-notification-banner__content">
                <p class="nhsuk-notification-banner__heading">Did a thing</p>
            </div>
        </div>
        """,
        html,
    )


def test_success_banner_with_html_message(jinja_env):
    template = jinja_env.from_string(
        """
        {% extends "layout-app.jinja" %}
        """
    )
    request = RequestFactory().get("/")
    request._messages = [
        Message(
            level=SUCCESS, message=mark_safe("<p>Did an <em>important</em> thing</p>")
        )
    ]

    html = template.render({"request": request})

    assertInHTML(
        """
        <div class="nhsuk-notification-banner nhsuk-notification-banner--success" role="alert" aria-labelledby="nhsuk-notification-banner-title" data-module="nhsuk-notification-banner" data-disable-auto-focus="true">
            <div class="nhsuk-notification-banner__header">
                <h2 class="nhsuk-notification-banner__title" id="nhsuk-notification-banner-title">Success</h2>
            </div>
            <div class="nhsuk-notification-banner__content">
                <p>Did an <em>important</em> thing</p>
            </div>
        </div>
        """,
        html,
    )
