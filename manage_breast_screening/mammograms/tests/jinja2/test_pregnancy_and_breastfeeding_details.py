from textwrap import dedent

import pytest
from pytest_django.asserts import assertHTMLEqual

from manage_breast_screening.mammograms.presenters.medical_information_presenter import (
    MedicalInformationPresenter,
)


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


def test_pregnancy_and_breastfeeding_none(template, mock_appointment):
    mock_appointment.pregnancy_and_breastfeeding = None
    response = template.render(
        {"presenter": MedicalInformationPresenter(mock_appointment)}
    )

    assertHTMLEqual(
        response,
        f"""
        <a href="/mammograms/{mock_appointment.pk}/record-medical-information/pregnancy-and-breastfeeding/">Enter pregnancy and breastfeeding details</a>
        """,
    )


def test_pregnancy_and_breastfeeding_no(template, mock_appointment):
    mock_appointment.pregnancy_and_breastfeeding = {
        "pregnancy_status": "NO",
        "breastfeeding_status": "NO",
    }

    response = template.render(
        {"presenter": MedicalInformationPresenter(mock_appointment)}
    )

    assertHTMLEqual(
        response,
        """
        <p>Not pregnant</p>
        <p>Not breastfeeding</p>
        """,
    )


def test_pregnancy_and_breastfeeding_yes(template, mock_appointment):
    mock_appointment.pregnancy_and_breastfeeding = {
        "pregnancy_status": "YES",
        "approx_pregnancy_due_date": "Autumn",
        "breastfeeding_status": "YES",
        "approx_breastfeeding_start_date": "1 year & 6 months",
    }

    response = template.render(
        {"presenter": MedicalInformationPresenter(mock_appointment)}
    )

    assertHTMLEqual(
        response,
        """
        <p>Currently pregnant</p>
        <p>Timeframe: Autumn</p>
        <p>Currently breastfeeding</p>
        <p>Details: 1 year &amp; 6 months</p>
        """,
    )


def test_pregnancy_yes(template, mock_appointment):
    mock_appointment.pregnancy_and_breastfeeding = {
        "pregnancy_status": "YES",
        "approx_pregnancy_due_date": "September",
        "breastfeeding_status": "NO",
    }

    response = template.render(
        {"presenter": MedicalInformationPresenter(mock_appointment)}
    )

    assertHTMLEqual(
        response,
        """
        <p>Currently pregnant</p>
        <p>Timeframe: September</p>
        <p>Not breastfeeding</p>
        """,
    )


def test_pregnancy_no_but_has_been_recently(template, mock_appointment):
    mock_appointment.pregnancy_and_breastfeeding = {
        "pregnancy_status": "NO_BUT_HAS_BEEN_RECENTLY",
        "approx_pregnancy_end_date": "3 months ago",
        "breastfeeding_status": "NO",
    }

    response = template.render(
        {"presenter": MedicalInformationPresenter(mock_appointment)}
    )

    assertHTMLEqual(
        response,
        """
        <p>Recently pregnant</p>
        <p>Details: 3 months ago</p>
        <p>Not breastfeeding</p>
        """,
    )


def test_breastfeeding_yes(template, mock_appointment):
    mock_appointment.pregnancy_and_breastfeeding = {
        "pregnancy_status": "NO",
        "breastfeeding_status": "YES",
        "approx_breastfeeding_start_date": "6 months",
    }

    response = template.render(
        {"presenter": MedicalInformationPresenter(mock_appointment)}
    )

    assertHTMLEqual(
        response,
        """
        <p>Not pregnant</p>
        <p>Currently breastfeeding</p>
        <p>Details: 6 months</p>
        """,
    )


def test_breastfeeding_no_but_stopped_recently(template, mock_appointment):
    mock_appointment.pregnancy_and_breastfeeding = {
        "pregnancy_status": "NO",
        "breastfeeding_status": "NO_BUT_STOPPED_RECENTLY",
        "approx_breastfeeding_end_date": "12 February",
    }

    response = template.render(
        {"presenter": MedicalInformationPresenter(mock_appointment)}
    )

    assertHTMLEqual(
        response,
        """
        <p>Not pregnant</p>
        <p>Recently breastfeeding</p>
        <p>Details: 12 February</p>
        """,
    )
