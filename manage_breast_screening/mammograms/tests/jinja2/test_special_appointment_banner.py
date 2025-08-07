from textwrap import dedent

import pytest
from pytest_django.asserts import assertHTMLEqual

from manage_breast_screening.mammograms.presenters import SpecialAppointmentPresenter


@pytest.fixture
def presenter():
    return SpecialAppointmentPresenter(
        {
            "PHYSICAL_RESTRICTION": {"details": "broken foot", "temporary": "True"},
            "SOCIAL_EMOTIONAL_MENTAL_HEALTH": {},
        },
        "68d758d0-792d-430f-9c52-1e7a0c2aa1dd",
    )


def test_special_appointment_banner_with_change_link(jinja_env, presenter):
    template = jinja_env.from_string(
        dedent(
            r"""
                {% from 'mammograms/special_appointments/special_appointment_banner.jinja' import special_appointment_banner %}
                {{ special_appointment_banner(presenter, show_change_link=True) }}
                """
        )
    )

    response = template.render({"presenter": presenter})

    assertHTMLEqual(
        response,
        """
        <div class="nhsuk-warning-callout">
            <h3 class="nhsuk-warning-callout__label">    <span role="text">
                <span class="nhsuk-u-visually-hidden">Important: </span>
                Special appointment
            </span></h3>

            <dl class="nhsuk-summary-list app-special-appointment-banner">
                <div class="nhsuk-summary-list__row">
                    <dt class="nhsuk-summary-list__key">
                    Physical restriction
                    </dt>
                    <dd class="nhsuk-summary-list__value">
                    broken foot<br><span class="app-special-appointment-banner__tag--temporary">Temporary</span>
                    </dd>
                </div>
                <div class="nhsuk-summary-list__row">
                    <dt class="nhsuk-summary-list__key">
                    Social, emotional, and mental health
                    </dt>
                    <dd class="nhsuk-summary-list__value">
                    <span class="app-special-appointment-banner__tag--no-details">No details provided</span>
                    </dd>
                </div>
            </dl>
            <div class="app-special-appointment-banner__action">
                <a href="/mammograms/68d758d0-792d-430f-9c52-1e7a0c2aa1dd/special-appointment/" style="font-size: 19px;">Change<span class="nhsuk-u-visually-hidden"> special appointment requirements</span></a>
            </div>
        </div>
    """,
    )


def test_special_appointment_banner_without_change_link(jinja_env, presenter):
    template = jinja_env.from_string(
        dedent(
            r"""
                {% from 'mammograms/special_appointments/special_appointment_banner.jinja' import special_appointment_banner %}
                {{ special_appointment_banner(presenter, show_change_link=False) }}
                """
        )
    )

    response = template.render({"presenter": presenter})

    assertHTMLEqual(
        response,
        """
        <div class="nhsuk-warning-callout">
            <h3 class="nhsuk-warning-callout__label">    <span role="text">
                <span class="nhsuk-u-visually-hidden">Important: </span>
                Special appointment
            </span></h3>

            <dl class="nhsuk-summary-list app-special-appointment-banner">
                <div class="nhsuk-summary-list__row">
                    <dt class="nhsuk-summary-list__key">
                    Physical restriction
                    </dt>
                    <dd class="nhsuk-summary-list__value">
                    broken foot<br><span class="app-special-appointment-banner__tag--temporary">Temporary</span>
                    </dd>
                </div>
                <div class="nhsuk-summary-list__row">
                    <dt class="nhsuk-summary-list__key">
                    Social, emotional, and mental health
                    </dt>
                    <dd class="nhsuk-summary-list__value">
                    <span class="app-special-appointment-banner__tag--no-details">No details provided</span>
                    </dd>
                </div>
            </dl>
        </div>
    """,
    )
