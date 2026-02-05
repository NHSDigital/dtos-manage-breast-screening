from textwrap import dedent

import pytest
from pytest_django.asserts import assertHTMLEqual


@pytest.fixture
def presenter():
    return {"content": "Some appointment note details."}


def test_appointment_note_banner_with_change_link(jinja_env, presenter):
    template = jinja_env.from_string(
        dedent(
            r"""
                {% from 'mammograms/appointment_notes/appointment_note_banner.jinja' import appointment_note_banner %}
                {{ appointment_note_banner(presenter, show_change_link=True, change_url="/change-url") }}
                """
        )
    )

    response = template.render({"presenter": presenter})

    assertHTMLEqual(
        response,
        """
        <div class="nhsuk-card nhsuk-card--warning">
        <div class="nhsuk-card__heading-container">
            <h3 class="nhsuk-card__heading">
            <span role="text">
                <span class="nhsuk-u-visually-hidden">Important:</span> Appointment note
            </span>
            </h3>
            <div class="nhsuk-card__actions">
            <a class="nhsuk-link nhsuk-link--no-visited-state" href="/change-url">Change<span class="nhsuk-u-visually-hidden">  note (Appointment note)</span></a>
            </div>
        </div>
        <div class="nhsuk-card__content">
            <div class="nhsuk-grid-row">
                    <div class="nhsuk-grid-column-two-thirds">
                    <p>Some appointment note details.</p>
                    </div>
                </div>
        </div>
        </div>
    """,
    )


def test_appointment_note_banner_without_change_link(jinja_env, presenter):
    template = jinja_env.from_string(
        dedent(
            r"""
                {% from 'mammograms/appointment_notes/appointment_note_banner.jinja' import appointment_note_banner %}
                {{ appointment_note_banner(presenter, show_change_link=False, change_url="/change-url") }}
                """
        )
    )

    response = template.render({"presenter": presenter})

    assertHTMLEqual(
        response,
        """
        <div class="nhsuk-card nhsuk-card--warning">
            <div class="nhsuk-card__content">
                <h3 class="nhsuk-card__heading">
                    <span role="text">
                        <span class="nhsuk-u-visually-hidden">Important:</span> Appointment note
                    </span>
                </h3>
                <div class="nhsuk-grid-row">
                    <div class="nhsuk-grid-column-two-thirds">
                        <p>Some appointment note details.</p>
                    </div>
                </div>
            </div>
        </div>
    """,
    )
