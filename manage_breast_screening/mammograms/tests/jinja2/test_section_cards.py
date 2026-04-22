from datetime import datetime, timezone
from textwrap import dedent

import pytest
import time_machine
from pytest_django.asserts import assertInHTML

from manage_breast_screening.mammograms.presenters import LastKnownMammogramPresenter
from manage_breast_screening.mammograms.presenters.medical_information_presenter import (
    MedicalInformationPresenter,
)
from manage_breast_screening.participants.models.reported_mammograms import (
    ParticipantReportedMammogram,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ConfirmedPreviousMammogramFactory,
    ParticipantReportedMammogramFactory,
)
from manage_breast_screening.users.tests.factories import UserFactory


@pytest.mark.django_db
class TestMammogramHistoryContent:
    @pytest.fixture
    def template(self, jinja_env):
        return jinja_env.from_string(
            dedent(
                r"""
                {% from 'mammograms/medical_information/section_cards.jinja' import mammogram_history_content %}
                {{ mammogram_history_content(presented_medical_info=presented_medical_info, presented_mammograms=presented_mammograms, read_only=read_only) }}
                """
            )
        )

    @time_machine.travel(datetime(2025, 1, 1, 10, tzinfo=timezone.utc))
    def test_mammogram_history_content_empty(self, template, user, mock_appointment):
        response = template.render(
            {
                "presented_medical_info": MedicalInformationPresenter(
                    appointment=mock_appointment
                ),
                "presented_mammograms": LastKnownMammogramPresenter(
                    appointment_pk=mock_appointment.pk,
                    user=user,
                    last_confirmed_mammogram=None,
                    reported_mammograms=[],
                    current_url="/",
                ),
                "read_only": False,
            }
        )
        assertInHTML(
            """
            <p>The last confirmed mammogram and any added manually since then</p>

            <h3 class="nhsuk-heading-s">From screening records</h3>
            <dl class="nhsuk-summary-list">
                <div class="nhsuk-summary-list__row">
                    <dt class="nhsuk-summary-list__key">
                        Last known mammogram
                    </dt>
                    <dd class="nhsuk-summary-list__value">
                        <span class="nhsuk-u-secondary-text-colour">Not known</span>
                    </dd>
                </div>
            </dl>

            <a class="nhsuk-button nhsuk-button--secondary nhsuk-button--small"
               data-module="nhsuk-button" 
               href="/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/previous-mammograms/add/?return_url=%2Fmammograms%2F53ce8d3b-9e65-471a-b906-73809c0475d0%2Frecord-medical-information%2F"
               role="button" draggable="false">
            Add another mammogram
            </a>
            """,
            response,
        )

    @time_machine.travel(datetime(2025, 1, 1, 10, tzinfo=timezone.utc))
    def test_mammogram_history_content_read_only(self, template):
        appointment = AppointmentFactory.create()
        user = UserFactory.create(
            nhs_uid="TestLastKnownMammogramPresenter",
            first_name="Xyz",
            last_name="Lastname",
        )
        mammogram = ParticipantReportedMammogramFactory.build(
            appointment=appointment,
            date_type=ParticipantReportedMammogram.DateType.EXACT,
            exact_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            location_type=ParticipantReportedMammogram.LocationType.SAME_PROVIDER,
            location_details="France",
            created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            created_by=user,
        )
        presented_mammograms = LastKnownMammogramPresenter(
            user=user,
            reported_mammograms=[mammogram],
            last_confirmed_mammogram=ConfirmedPreviousMammogramFactory.create(),
            appointment_pk=appointment.pk,
            current_url="/",
        )
        response = template.render(
            {
                "presented_medical_info": MedicalInformationPresenter(
                    appointment=appointment
                ),
                "presented_mammograms": presented_mammograms,
                "read_only": True,
            }
        )

        assertInHTML(
            f"""
            <p>The last confirmed mammogram and any added manually since then</p>

            <h3 class="nhsuk-heading-s">From screening records</h3>
            <dl class="nhsuk-summary-list">
            <div class="nhsuk-summary-list__row">
                <dt class="nhsuk-summary-list__key">
                Last known mammogram
                </dt>
                <dd class="nhsuk-summary-list__value">
                1 January 2020 <span class="nhsuk-u-secondary-text-colour">(5 years ago)</span>
                <br>Some details about the previous mammogram
                </dd>
            </div>
            </dl>


            <h3 class="nhsuk-heading-s">Reported mammograms</h3>
            <dl class="nhsuk-summary-list">
            <div class="nhsuk-summary-list__row">
                <dt class="nhsuk-summary-list__key">
                    Recorded 1 January 2025<br>
                    <span class="nhsuk-u-secondary-text-colour nhsuk-body-s nhsuk-u-margin-bottom-0">
                        by X. Lastname (you)
                    </span>
                </dt>
                <dd class="nhsuk-summary-list__value">
                1 January 2025 <span class="nhsuk-u-secondary-text-colour">(today)</span>

                <br>{appointment.provider.name}
                </dd>
            </div>
            </dl>
            """,
            response,
        )

    @time_machine.travel(datetime(2025, 1, 1, 10, tzinfo=timezone.utc))
    def test_mammogram_history_content(self, template):
        appointment = AppointmentFactory.create()
        user = UserFactory.create(
            nhs_uid="TestLastKnownMammogramPresenter2",
            first_name="Xyz",
            last_name="Lastname",
        )
        mammogram1 = ParticipantReportedMammogramFactory.build(
            appointment=appointment,
            date_type=ParticipantReportedMammogram.DateType.EXACT,
            exact_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            location_type=ParticipantReportedMammogram.LocationType.SAME_PROVIDER,
            location_details="France",
            created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            created_by=user,
        )
        mammogram2 = ParticipantReportedMammogramFactory.build(
            appointment=appointment,
            date_type=ParticipantReportedMammogram.DateType.LESS_THAN_SIX_MONTHS,
            approx_date="2021",
            location_type=ParticipantReportedMammogram.LocationType.ANOTHER_NHS_PROVIDER,
            location_details="France",
            created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            created_by=user,
        )
        mammogram3 = ParticipantReportedMammogramFactory.build(
            appointment=appointment,
            date_type=ParticipantReportedMammogram.DateType.MORE_THAN_SIX_MONTHS,
            approx_date="2021",
            location_type=ParticipantReportedMammogram.LocationType.ELSEWHERE_UK,
            location_details="France",
            created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            created_by=user,
        )
        mammogram4 = ParticipantReportedMammogramFactory.build(
            appointment=appointment,
            date_type=ParticipantReportedMammogram.DateType.MORE_THAN_SIX_MONTHS,
            approx_date="2021",
            location_type=ParticipantReportedMammogram.LocationType.OUTSIDE_UK,
            location_details="Yorkshire",
            created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            created_by=user,
        )
        mammogram5 = ParticipantReportedMammogramFactory.build(
            appointment=appointment,
            date_type=ParticipantReportedMammogram.DateType.MORE_THAN_SIX_MONTHS,
            approx_date="2021",
            location_type=ParticipantReportedMammogram.LocationType.PREFER_NOT_TO_SAY,
            created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            created_by=user,
        )

        presented_mammograms = LastKnownMammogramPresenter(
            user=user,
            reported_mammograms=[
                mammogram1,
                mammogram2,
                mammogram3,
                mammogram4,
                mammogram5,
            ],
            last_confirmed_mammogram=ConfirmedPreviousMammogramFactory.create(),
            appointment_pk=appointment.pk,
            current_url="/",
        )

        response = template.render(
            {
                "presented_medical_info": MedicalInformationPresenter(
                    appointment=appointment
                ),
                "presented_mammograms": presented_mammograms,
            }
        )

        assertInHTML(
            f"""
            <p>The last confirmed mammogram and any added manually since then</p>

            <h3 class="nhsuk-heading-s">From screening records</h3>
            <dl class="nhsuk-summary-list">
            <div class="nhsuk-summary-list__row">
                <dt class="nhsuk-summary-list__key">
                Last known mammogram
                </dt>
                <dd class="nhsuk-summary-list__value">
                1 January 2020 <span class="nhsuk-u-secondary-text-colour">(5 years ago)</span>
                <br>Some details about the previous mammogram
                </dd>
            </div>
            </dl>

            <h3 class="nhsuk-heading-s">Reported mammograms</h3>
            <dl class="nhsuk-summary-list">
            <div class="nhsuk-summary-list__row">
                <dt class="nhsuk-summary-list__key">
                    Recorded 1 January 2025<br>
                    <span class="nhsuk-u-secondary-text-colour nhsuk-body-s nhsuk-u-margin-bottom-0">
                        by X. Lastname (you)
                    </span>
                </dt>
                <dd class="nhsuk-summary-list__value">
                1 January 2025 <span class="nhsuk-u-secondary-text-colour">(today)</span>

                <br>{appointment.provider.name}
                </dd>
                <dd class="nhsuk-summary-list__actions">
                <a class="nhsuk-link nhsuk-link--no-visited-state"
                    href="/mammograms/{appointment.pk}/previous-mammograms/{mammogram1.pk}/?return_url=/">Change<span
                    class="nhsuk-u-visually-hidden"> mammogram item 1</span></a>
                </dd>
            </div>
            <div class="nhsuk-summary-list__row">
                <dt class="nhsuk-summary-list__key">
                    Recorded 1 January 2025<br>
                    <span class="nhsuk-u-secondary-text-colour nhsuk-body-s nhsuk-u-margin-bottom-0">
                        by X. Lastname (you)
                    </span>
                </dt>
                <dd class="nhsuk-summary-list__value">
                Taken less than 6 months ago: 2021

                <br>NHS BSU: France
                </dd>
                <dd class="nhsuk-summary-list__actions">
                <a class="nhsuk-link nhsuk-link--no-visited-state"
                    href="/mammograms/{appointment.pk}/previous-mammograms/{mammogram2.pk}/?return_url=/">Change<span
                    class="nhsuk-u-visually-hidden"> mammogram item 2</span></a>
                </dd>
            </div>
            <div class="nhsuk-summary-list__row">
                <dt class="nhsuk-summary-list__key">
                    Recorded 1 January 2025<br>
                    <span class="nhsuk-u-secondary-text-colour nhsuk-body-s nhsuk-u-margin-bottom-0">
                        by X. Lastname (you)
                    </span>
                </dt>
                <dd class="nhsuk-summary-list__value">
                Taken 6 months or more ago: 2021

                <br>In the UK: France
                </dd>
                <dd class="nhsuk-summary-list__actions">
                <a class="nhsuk-link nhsuk-link--no-visited-state"
                    href="/mammograms/{appointment.pk}/previous-mammograms/{mammogram3.pk}/?return_url=/">Change<span
                    class="nhsuk-u-visually-hidden"> mammogram item 3</span></a>
                </dd>
            </div>
            <div class="nhsuk-summary-list__row">
                <dt class="nhsuk-summary-list__key">
                    Recorded 1 January 2025<br>
                    <span class="nhsuk-u-secondary-text-colour nhsuk-body-s nhsuk-u-margin-bottom-0">
                        by X. Lastname (you)
                    </span>
                </dt>
                <dd class="nhsuk-summary-list__value">
                Taken 6 months or more ago: 2021

                <br>Outside the UK: Yorkshire
                </dd>
                <dd class="nhsuk-summary-list__actions">
                <a class="nhsuk-link nhsuk-link--no-visited-state"
                    href="/mammograms/{appointment.pk}/previous-mammograms/{mammogram4.pk}/?return_url=/">Change<span
                    class="nhsuk-u-visually-hidden"> mammogram item 4</span></a>
                </dd>
            </div>
            <div class="nhsuk-summary-list__row">
                <dt class="nhsuk-summary-list__key">
                    Recorded 1 January 2025<br>
                    <span class="nhsuk-u-secondary-text-colour nhsuk-body-s nhsuk-u-margin-bottom-0">
                        by X. Lastname (you)
                    </span>
                </dt>
                <dd class="nhsuk-summary-list__value">
                Taken 6 months or more ago: 2021

                <br>Location: prefer not to say
                </dd>
                <dd class="nhsuk-summary-list__actions">
                <a class="nhsuk-link nhsuk-link--no-visited-state"
                    href="/mammograms/{appointment.pk}/previous-mammograms/{mammogram5.pk}/?return_url=/">Change<span
                    class="nhsuk-u-visually-hidden"> mammogram item 5</span></a>
                </dd>
            </div>
            </dl>

            <a class="nhsuk-button nhsuk-button--secondary nhsuk-button--small" data-module="nhsuk-button"
            href="/mammograms/{appointment.pk}/previous-mammograms/add/?return_url=%2Fmammograms%2F{appointment.pk}%2Frecord-medical-information%2F"
            role="button" draggable="false">
            Add another mammogram
            </a>
            """,
            response,
        )
