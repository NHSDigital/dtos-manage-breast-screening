from textwrap import dedent
from unittest.mock import MagicMock

import pytest
from pytest_django.asserts import assertInHTML

from manage_breast_screening.participants.presenters import (
    ParticipantAppointmentsPresenter,
)


class TestAppointments:
    @pytest.fixture
    def upcoming(self):
        return [
            ParticipantAppointmentsPresenter.PresentedAppointment(
                "1 January 2025",
                "Screening",
                "West of London BSS",
                {
                    "classes": "nhsuk-tag--blue app-u-nowrap",
                    "key": "CONFIRMED",
                    "text": "Confirmed",
                },
                "/mammograms/e3d475a6-c405-44d6-bbd7-bcb5cd4d4996/",
            )
        ]

    @pytest.fixture
    def past(self):
        return [
            ParticipantAppointmentsPresenter.PresentedAppointment(
                "1 January 2023",
                "Screening",
                "West of London BSS",
                {
                    "classes": "nhsuk-tag--orange app-u-nowrap",
                    "key": "PARTIALLY_SCREENED",
                    "text": "Partially screened",
                },
                "/mammograms/e76163c8-a594-4991-890d-a02097c67a2f/",
            ),
            ParticipantAppointmentsPresenter.PresentedAppointment(
                "1 January 2019",
                "Screening",
                "West of London BSS",
                {
                    "classes": "nhsuk-tag--green app-u-nowrap",
                    "key": "SCREENED",
                    "text": "Screened",
                },
                "/mammograms/6473a629-e7c4-43ca-87f3-ab9526aab07c/",
            ),
        ]

    @pytest.fixture
    def presenter(self, upcoming, past):
        mock = MagicMock(spec=ParticipantAppointmentsPresenter)
        mock.upcoming = upcoming
        mock.past = past
        return mock

    def test_upcoming(self, presenter, jinja_env):
        template = jinja_env.from_string(
            dedent(
                r"""
                {% from 'components/participant-details/appointments.jinja' import appointments %}
                {{ appointments(presenter) }}
                """
            )
        )

        response = template.render({"presenter": presenter})

        assertInHTML("<h3>Upcoming</h3>", response)
        assertInHTML("<h3>Previous</h3>", response)
        assertInHTML(
            """
                            <td>1 January 2025</td>
                            <td>Screening</td>
                            <td>West of London BSS</td>
                            <td><strong class="app-u-nowrap nhsuk-tag nhsuk-tag--blue">Confirmed</strong></td>
                            <td><a href="/mammograms/e3d475a6-c405-44d6-bbd7-bcb5cd4d4996/">View details</a></td>
        """,
            response,
        )
        assertInHTML(
            """
                    <td>1 January 2023</td>
                    <td>Screening</td>
                    <td>West of London BSS</td>
                    <td><strong class="app-u-nowrap nhsuk-tag nhsuk-tag--orange">Partially screened</strong></td>
                    <td><a href="/mammograms/e76163c8-a594-4991-890d-a02097c67a2f/">View details</a></td>
""",
            response,
        )
        assertInHTML(
            """
                    <td>1 January 2019</td>
                    <td>Screening</td>
                    <td>West of London BSS</td>
                    <td><strong class="app-u-nowrap nhsuk-tag nhsuk-tag--green">Screened</strong></td>
                    <td><a href="/mammograms/6473a629-e7c4-43ca-87f3-ab9526aab07c/">View details</a></td>
""",
            response,
        )
