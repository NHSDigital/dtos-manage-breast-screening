from textwrap import dedent

import pytest
from pytest_django.asserts import assertHTMLEqual

from manage_breast_screening.mammograms.presenters.appointment_presenters import (
    AppointmentPresenter,
)


@pytest.fixture
def template(jinja_env):
    return jinja_env.from_string(
        dedent(
            r"""
                {% from 'mammograms/check_information/appointment_details_card.jinja' import appointment_details_card %}
                {{ appointment_details_card(presenter) }}
                """
        )
    )


def test_appointment_details_empty(template, mock_appointment):
    mock_appointment.screening_episode.participant.extra_needs = {}
    presenter = AppointmentPresenter(mock_appointment)
    presenter.__dict__["has_appointment_note"] = False

    response = template.render({"presenter": presenter})

    assertHTMLEqual(
        response,
        """
        <div class="nhsuk-card nhsuk-card--feature">
            <div class="nhsuk-card__content">
                <h2 class="nhsuk-card__heading">
                    Appointment details
                </h2>
                <dl class="nhsuk-summary-list">
                    <div class="nhsuk-summary-list__row">
                        <dt class="nhsuk-summary-list__key">
                            Special appointment
                        </dt>
                        <dd class="nhsuk-summary-list__value">
                            No
                        </dd>
                        <dd class="nhsuk-summary-list__actions">
                            <a class="nhsuk-link nhsuk-link--no-visited-state" href="/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/special-appointment/?return_url=">
                                Change<span class="nhsuk-u-visually-hidden"> special appointment</span>
                            </a>
                        </dd>
                    </div>
                    <div class="nhsuk-summary-list__row nhsuk-summary-list__row--no-actions">
                        <dt class="nhsuk-summary-list__key">
                            Appointment note
                        </dt>
                        <dd class="nhsuk-summary-list__value">
                            <a href="/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/note-review/?return_url=" class="nhsuk-link">
                                Enter appointment note
                            </a>
                        </dd>
                    </div>
                </dl>
            </div>
        </div>
    """,
    )


def test_appointment_details_is_special_appointmet(template, mock_appointment):
    mock_appointment.screening_episode.participant.extra_needs = {
        "BREAST_IMPLANTS": {
            "details": "details of\nbreast implants",
        },
        "MEDICAL_DEVICES": {"details": "has pacemaker"},
        "OTHER": {"details": "Other details."},
    }
    presenter = AppointmentPresenter(mock_appointment)
    presenter.__dict__["has_appointment_note"] = False

    response = template.render({"presenter": presenter})

    assertHTMLEqual(
        response,
        """
        <div class="nhsuk-card nhsuk-card--feature">
            <div class="nhsuk-card__content">
                <h2 class="nhsuk-card__heading">
                Appointment details
                </h2>
                <dl class="nhsuk-summary-list">
                    <div class="nhsuk-summary-list__row">
                        <dt class="nhsuk-summary-list__key">
                            Special appointment
                        </dt>
                        <dd class="nhsuk-summary-list__value">
                            <strong class="nhsuk-tag nhsuk-tag--yellow nhsuk-u-margin-top-2">
                                Special appointment
                            </strong>
                            <p class="nhsuk-u-margin-bottom-2">
                                <strong>Breast implants</strong><br>
                                details of<br>breast implants
                            </p>
                            <p class="nhsuk-u-margin-bottom-2">
                                <strong>Implanted medical devices</strong><br>
                                has pacemaker
                            </p>
                            <p class="nhsuk-u-margin-bottom-2">
                                <strong>Other</strong><br>
                                Other details.
                            </p>
                        </dd>
                        <dd class="nhsuk-summary-list__actions">
                            <a class="nhsuk-link nhsuk-link--no-visited-state" href="/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/special-appointment/?return_url=">
                                Change<span class="nhsuk-u-visually-hidden"> special appointment</span>
                            </a>
                        </dd>
                    </div>
                    <div class="nhsuk-summary-list__row nhsuk-summary-list__row--no-actions">
                        <dt class="nhsuk-summary-list__key">
                            Appointment note
                        </dt>
                        <dd class="nhsuk-summary-list__value">
                            <a href="/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/note-review/?return_url=" class="nhsuk-link">
                                Enter appointment note
                            </a>
                        </dd>
                    </div>
                </dl>
            </div>
        </div>
    """,
    )


def test_appointment_details_has_appointment_note(template, mock_appointment):
    mock_appointment.screening_episode.participant.extra_needs = {}
    mock_appointment.note.content = "a note about\nthe appointment"

    response = template.render({"presenter": AppointmentPresenter(mock_appointment)})

    assertHTMLEqual(
        response,
        """
        <div class="nhsuk-card nhsuk-card--feature">
            <div class="nhsuk-card__content">
                <h2 class="nhsuk-card__heading">
                    Appointment details
                </h2>
                <dl class="nhsuk-summary-list">
                    <div class="nhsuk-summary-list__row">
                        <dt class="nhsuk-summary-list__key">
                            Special appointment
                        </dt>
                        <dd class="nhsuk-summary-list__value">
                            No
                        </dd>
                        <dd class="nhsuk-summary-list__actions">
                            <a class="nhsuk-link nhsuk-link--no-visited-state" href="/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/special-appointment/?return_url=">
                                Change<span class="nhsuk-u-visually-hidden"> special appointment</span>
                            </a>
                        </dd>
                    </div>
                    <div class="nhsuk-summary-list__row">
                        <dt class="nhsuk-summary-list__key">
                            Appointment note
                        </dt>
                        <dd class="nhsuk-summary-list__value">
                            a note about<br>the appointment
                        </dd>
                        <dd class="nhsuk-summary-list__actions">
                            <a class="nhsuk-link nhsuk-link--no-visited-state" href="/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/note-review/?return_url=">
                                Change<span class="nhsuk-u-visually-hidden"> appointment note</span>
                            </a>
                        </dd>
                    </div>
                </dl>
            </div>
        </div>
    """,
    )


def test_appointment_details_special_appointment_with_note(template, mock_appointment):
    mock_appointment.screening_episode.participant.extra_needs = {
        "SOCIAL_EMOTIONAL_MENTAL_HEALTH": {
            "details": "Social, emotional & mental health",
        },
    }
    mock_appointment.note.content = (
        "Things to consider before & during the appointment."
    )

    response = template.render({"presenter": AppointmentPresenter(mock_appointment)})

    assertHTMLEqual(
        response,
        """
        <div class="nhsuk-card nhsuk-card--feature">
            <div class="nhsuk-card__content">
                <h2 class="nhsuk-card__heading">
                    Appointment details
                </h2>
                <dl class="nhsuk-summary-list">
                    <div class="nhsuk-summary-list__row">
                        <dt class="nhsuk-summary-list__key">
                            Special appointment
                        </dt>
                        <dd class="nhsuk-summary-list__value">
                            <strong class="nhsuk-tag nhsuk-tag--yellow nhsuk-u-margin-top-2">
                                Special appointment
                            </strong>
                            <p class="nhsuk-u-margin-bottom-2">
                                <strong>Social, emotional, and mental health</strong><br>
                                Social, emotional &amp; mental health
                            </p>
                        </dd>
                        <dd class="nhsuk-summary-list__actions">
                            <a class="nhsuk-link nhsuk-link--no-visited-state" href="/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/special-appointment/?return_url=">
                                Change<span class="nhsuk-u-visually-hidden"> special appointment</span>
                            </a>
                        </dd>
                    </div>
                    <div class="nhsuk-summary-list__row">
                        <dt class="nhsuk-summary-list__key">
                            Appointment note
                        </dt>
                        <dd class="nhsuk-summary-list__value">
                            Things to consider before &amp; during the appointment.
                        </dd>
                        <dd class="nhsuk-summary-list__actions">
                            <a class="nhsuk-link nhsuk-link--no-visited-state" href="/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/note-review/?return_url=">
                                Change<span class="nhsuk-u-visually-hidden"> appointment note</span>
                            </a>
                        </dd>
                    </div>
                </dl>
            </div>
        </div>
    """,
    )
