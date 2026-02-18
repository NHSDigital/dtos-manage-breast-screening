from textwrap import dedent
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from pytest_django.asserts import assertHTMLEqual

from manage_breast_screening.mammograms.presenters.medical_information_presenter import (
    MedicalInformationPresenter,
)
from manage_breast_screening.participants.models.appointment import Appointment


@pytest.fixture
def appointment():
    mock_appointment = MagicMock(spec=Appointment)
    mock_appointment.pk = "53ce8d3b-9e65-471a-b906-73809c0475d0"
    mock_appointment.screening_episode.participant.nhs_number = "99900900829"
    mock_appointment.screening_episode.participant.pk = uuid4()
    mock_appointment.screening_episode.participant.phone = "01234123456"
    return mock_appointment


@pytest.fixture
def template(jinja_env):
    return jinja_env.from_string(
        dedent(
            r"""
            {% from 'mammograms/medical_information/other_information/cards/macros.jinja' import hormone_replacement_therapy_details %}
            {{ hormone_replacement_therapy_details(presenter) }}
            """
        )
    )


def test_hormone_replacement_therapy_none(template, appointment):
    appointment.hormone_replacement_therapy = None
    response = template.render({"presenter": MedicalInformationPresenter(appointment)})

    assertHTMLEqual(
        response,
        f"""
        <a href="/mammograms/{appointment.pk}/record-medical-information/hormone-replacement-therapy/">Enter hormone replacement therapy (HRT) details</a>
        """,
    )


def test_hormone_replacement_therapy_yes(template, appointment):
    appointment.hormone_replacement_therapy = {
        "status": "YES",
        "approx_start_date": "Early 2010",
    }

    response = template.render({"presenter": MedicalInformationPresenter(appointment)})

    assertHTMLEqual(response, "<p>Taking HRT (Early 2010)</p>")


def test_hormone_replacement_therapy_no_but_stopped_recently(template, appointment):
    appointment.hormone_replacement_therapy = {
        "status": "NO_BUT_STOPPED_RECENTLY",
        "approx_previous_duration": "6 months",
        "approx_end_date": "2024-05-01",
    }

    response = template.render({"presenter": MedicalInformationPresenter(appointment)})

    assertHTMLEqual(response, "<p>Recently stopped HRT (2024-05-01)</p>")


def test_hormone_replacement_therapy_no(template, appointment):
    appointment.hormone_replacement_therapy = {"status": "NO"}

    response = template.render({"presenter": MedicalInformationPresenter(appointment)})

    assertHTMLEqual(response, "<p>Not taking HRT</p>")
