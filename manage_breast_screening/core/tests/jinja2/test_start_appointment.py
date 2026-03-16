from unittest.mock import MagicMock

import pytest


@pytest.fixture
def template(jinja_env):
    return jinja_env.get_template("components/start-appointment/template.jinja")


@pytest.fixture
def presented_appointment():
    mock = MagicMock()
    mock.pk = "abc-123"
    mock.participant.full_name = "Jane Smith"
    mock.can_be_checked_in = False
    return mock


def render(template, user_has_perm, presented_appointment):
    user = MagicMock()
    user.has_perm.return_value = user_has_perm
    return template.render(
        {
            "user": user,
            "presented_appointment": presented_appointment,
            "start_appointment_url": "/mammograms/abc-123/start-appointment/",
            "csrf_input": "",
        }
    )


def test_renders_start_button_for_clinical_user(template, presented_appointment):
    html = render(
        template, user_has_perm=True, presented_appointment=presented_appointment
    )
    assert 'data-module="app-start-appointment"' in html


def test_does_not_render_start_button_for_admin_user(template, presented_appointment):
    html = render(
        template, user_has_perm=False, presented_appointment=presented_appointment
    )
    assert 'data-module="app-start-appointment"' not in html


def test_renders_button_hidden_before_checkin(template, presented_appointment):
    presented_appointment.can_be_checked_in = True
    html = render(
        template, user_has_perm=True, presented_appointment=presented_appointment
    )
    assert 'data-module="app-start-appointment"' in html
    assert 'data-appointment-id="abc-123" hidden' in html


def test_renders_button_visible_after_checkin(template, presented_appointment):
    presented_appointment.can_be_checked_in = False
    html = render(
        template, user_has_perm=True, presented_appointment=presented_appointment
    )
    assert 'data-module="app-start-appointment"' in html
    assert 'data-appointment-id="abc-123" hidden' not in html
