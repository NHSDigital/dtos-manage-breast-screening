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
            {% from 'mammograms/medical_information/other_information/cards/macros.jinja' import pregnancy_and_breastfeeding_details %}
            {{ pregnancy_and_breastfeeding_details(presenter) }}
            """
        )
    )


def test_pregnancy_and_breastfeeding_none(template, appointment):
    appointment.pregnancy_and_breastfeeding = None
    response = template.render({"presenter": MedicalInformationPresenter(appointment)})

    assertHTMLEqual(
        response,
        f"""
        <a href="/mammograms/{appointment.pk}/record-medical-information/pregnancy-and-breastfeeding/">Enter pregnancy and breastfeeding details</a>
        """,
    )


def test_pregnancy_and_breastfeeding_no(template, appointment):
    appointment.pregnancy_and_breastfeeding = {
        "pregnancy_status": "NO",
        "breastfeeding_status": "NO",
    }

    response = template.render({"presenter": MedicalInformationPresenter(appointment)})

    assertHTMLEqual(
        response,
        """
        <p>Not pregnant</p>
        <p>Not breastfeeding</p>
        """,
    )


def test_pregnancy_and_breastfeeding_yes(template, appointment):
    appointment.pregnancy_and_breastfeeding = {
        "pregnancy_status": "YES",
        "approx_pregnancy_due_date": "Autumn",
        "breastfeeding_status": "YES",
        "approx_breastfeeding_start_date": "1 year & 6 months",
    }

    response = template.render({"presenter": MedicalInformationPresenter(appointment)})

    assertHTMLEqual(
        response,
        """
        <p>Currently pregnant</p>
        <p>Timeframe: Autumn</p>
        <p>Currently breastfeeding</p>
        <p>Details: 1 year &amp; 6 months</p>
        """,
    )


def test_pregnancy_yes(template, appointment):
    appointment.pregnancy_and_breastfeeding = {
        "pregnancy_status": "YES",
        "approx_pregnancy_due_date": "September",
        "breastfeeding_status": "NO",
    }

    response = template.render({"presenter": MedicalInformationPresenter(appointment)})

    assertHTMLEqual(
        response,
        """
        <p>Currently pregnant</p>
        <p>Timeframe: September</p>
        <p>Not breastfeeding</p>
        """,
    )


def test_pregnancy_no_but_has_been_recently(template, appointment):
    appointment.pregnancy_and_breastfeeding = {
        "pregnancy_status": "NO_BUT_HAS_BEEN_RECENTLY",
        "approx_pregnancy_end_date": "3 months ago",
        "breastfeeding_status": "NO",
    }

    response = template.render({"presenter": MedicalInformationPresenter(appointment)})

    assertHTMLEqual(
        response,
        """
        <p>Recently pregnant</p>
        <p>Details: 3 months ago</p>
        <p>Not breastfeeding</p>
        """,
    )


def test_breastfeeding_yes(template, appointment):
    appointment.pregnancy_and_breastfeeding = {
        "pregnancy_status": "NO",
        "breastfeeding_status": "YES",
        "approx_breastfeeding_start_date": "6 months",
    }

    response = template.render({"presenter": MedicalInformationPresenter(appointment)})

    assertHTMLEqual(
        response,
        """
        <p>Not pregnant</p>
        <p>Currently breastfeeding</p>
        <p>Details: 6 months</p>
        """,
    )


def test_breastfeeding_no_but_stopped_recently(template, appointment):
    appointment.pregnancy_and_breastfeeding = {
        "pregnancy_status": "NO",
        "breastfeeding_status": "NO_BUT_STOPPED_RECENTLY",
        "approx_breastfeeding_end_date": "12 February",
    }

    response = template.render({"presenter": MedicalInformationPresenter(appointment)})

    assertHTMLEqual(
        response,
        """
        <p>Not pregnant</p>
        <p>Recently breastfeeding</p>
        <p>Details: 12 February</p>
        """,
    )
