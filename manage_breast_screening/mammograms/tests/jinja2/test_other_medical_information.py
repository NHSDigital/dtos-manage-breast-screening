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
            {% from 'mammograms/medical_information/other_information/cards/macros.jinja' import other_medical_information_details %}
            {{ other_medical_information_details(presenter) }}
            """
        )
    )


def test_other_medical_information_none(template, mock_appointment):
    mock_appointment.other_medical_information = None
    response = template.render(
        {"presenter": MedicalInformationPresenter(mock_appointment)}
    )

    assertHTMLEqual(
        response,
        f"""
        <a href="/mammograms/{mock_appointment.pk}/record-medical-information/other-medical-information/">Enter other medical information details</a>
        """,
    )


def test_other_medical_information(template, mock_appointment):
    mock_appointment.other_medical_information = {
        "details": "other medical information details\nfor this participant"
    }

    response = template.render(
        {"presenter": MedicalInformationPresenter(mock_appointment)}
    )

    assertHTMLEqual(
        response, "other medical information details<br>for this participant"
    )
