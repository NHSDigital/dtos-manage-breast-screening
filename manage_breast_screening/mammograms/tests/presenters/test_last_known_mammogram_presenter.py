from datetime import date, datetime
from datetime import timezone as tz
from uuid import uuid4

import pytest
import time_machine

from manage_breast_screening.core.tests.factories import UserFactory
from manage_breast_screening.mammograms.presenters import LastKnownMammogramPresenter
from manage_breast_screening.participants.models import ParticipantReportedMammogram
from manage_breast_screening.participants.models.confirmed_mammograms import (
    ConfirmedPreviousMammogram,
)


@pytest.mark.django_db
class TestLastKnownMammogramPresenter:
    @pytest.fixture
    def reported_today(self, user, in_progress_appointment):
        return ParticipantReportedMammogram(
            created_at=datetime(2025, 1, 1),
            appointment=in_progress_appointment,
            location_type=ParticipantReportedMammogram.LocationType.ELSEWHERE_UK,
            location_details="Somewhere",
            date_type=ParticipantReportedMammogram.DateType.EXACT,
            exact_date=date(2022, 1, 1),
            created_by=user,
        )

    @pytest.fixture
    def reported_earlier(self, in_progress_appointment):
        return ParticipantReportedMammogram(
            created_at=datetime(2022, 1, 1),
            appointment=in_progress_appointment,
            location_type=ParticipantReportedMammogram.LocationType.SAME_PROVIDER,
            date_type=ParticipantReportedMammogram.DateType.MORE_THAN_SIX_MONTHS,
            approx_date="3 years ago",
            additional_information="Abcd",
            different_name="Janet Williams",
            reason_for_continuing="A reason",
            created_by=UserFactory.create(
                nhs_uid="TestLastKnownMammogramPresenter",
                first_name="Xyz",
                last_name="Lastname",
            ),
        )

    @time_machine.travel(datetime(2025, 1, 1, tzinfo=tz.utc))
    def test_no_last_known_mammograms(self, user):
        result = LastKnownMammogramPresenter(
            user=user,
            reported_mammograms=[],
            last_confirmed_mammogram=None,
            appointment_pk=uuid4(),
            current_url="/mammograms/abc",
        )

        assert result.reported_mammograms == []

    @time_machine.travel(datetime(2025, 1, 1, tzinfo=tz.utc))
    def test_last_known_mammograms_single(self, user, reported_today):
        appointment_pk = uuid4()
        result = LastKnownMammogramPresenter(
            user=user,
            reported_mammograms=[reported_today],
            last_confirmed_mammogram=None,
            appointment_pk=appointment_pk,
            current_url="/mammograms/abc",
        )

        assert result.reported_mammograms == [
            {
                "label": "Recorded 1 January 2025",
                "created_by": f"by {user.get_short_name()} (you)",
                "date_added": "today",
                "location": "In the UK: Somewhere",
                "date": {
                    "absolute": "1 January 2022",
                    "relative": "3 years ago",
                    "is_exact": True,
                },
                "different_name": "",
                "additional_information": "",
                "change_link": {
                    "href": f"/mammograms/{appointment_pk}/previous-mammograms/{reported_today.pk}?return_url=/mammograms/abc",
                    "text": "Change",
                    "visuallyHiddenText": "mammogram item",
                    "classes": "nhsuk-link--no-visited-state",
                },
                "reason_for_continuing": "",
            }
        ]

    @time_machine.travel(datetime(2025, 1, 1, tzinfo=tz.utc))
    def test_last_known_mammograms_another_nhs_unit(
        self, user, in_progress_appointment
    ):
        appointment_pk = uuid4()
        mammogram = ParticipantReportedMammogram(
            created_at=datetime(2025, 1, 1),
            created_by=user,
            appointment=in_progress_appointment,
            location_type=ParticipantReportedMammogram.LocationType.ANOTHER_NHS_PROVIDER,
            location_details="Old provider",
            date_type=ParticipantReportedMammogram.DateType.EXACT,
            exact_date=date(2022, 1, 1),
        )
        result = LastKnownMammogramPresenter(
            user=user,
            reported_mammograms=[mammogram],
            last_confirmed_mammogram=None,
            appointment_pk=appointment_pk,
            current_url="/mammograms/abc",
        )

        assert result.reported_mammograms == [
            {
                "label": "Recorded 1 January 2025",
                "created_by": f"by {user.get_short_name()} (you)",
                "date_added": "today",
                "location": "NHS BSU: Old provider",
                "date": {
                    "absolute": "1 January 2022",
                    "relative": "3 years ago",
                    "is_exact": True,
                },
                "different_name": "",
                "additional_information": "",
                "change_link": {
                    "href": f"/mammograms/{appointment_pk}/previous-mammograms/{mammogram.pk}?return_url=/mammograms/abc",
                    "text": "Change",
                    "visuallyHiddenText": "mammogram item",
                    "classes": "nhsuk-link--no-visited-state",
                },
                "reason_for_continuing": "",
            }
        ]

    @time_machine.travel(datetime(2025, 1, 1, tzinfo=tz.utc))
    def test_last_known_mammograms_multiple(
        self, user, in_progress_appointment, reported_today, reported_earlier
    ):
        appointment_pk = uuid4()
        result = LastKnownMammogramPresenter(
            user=user,
            reported_mammograms=[reported_today, reported_earlier],
            last_confirmed_mammogram=None,
            appointment_pk=appointment_pk,
            current_url="/mammograms/abc",
        )

        assert result.reported_mammograms == [
            {
                "label": "Recorded 1 January 2025",
                "created_by": f"by {user.get_short_name()} (you)",
                "date_added": "today",
                "location": "In the UK: Somewhere",
                "date": {
                    "absolute": "1 January 2022",
                    "relative": "3 years ago",
                    "is_exact": True,
                },
                "different_name": "",
                "additional_information": "",
                "change_link": {
                    "href": f"/mammograms/{appointment_pk}/previous-mammograms/{reported_today.pk}?return_url=/mammograms/abc",
                    "text": "Change",
                    "visuallyHiddenText": "mammogram item 1",
                    "classes": "nhsuk-link--no-visited-state",
                },
                "reason_for_continuing": "",
            },
            {
                "label": "Recorded 1 January 2022",
                "created_by": f"by {reported_earlier.created_by.get_short_name()}",
                "date_added": "3 years ago",
                "location": in_progress_appointment.provider.name,
                "date": {"value": "Taken 6 months or more ago: 3 years ago"},
                "different_name": "Janet Williams",
                "additional_information": "Abcd",
                "change_link": {
                    "href": f"/mammograms/{appointment_pk}/previous-mammograms/{reported_earlier.pk}?return_url=/mammograms/abc",
                    "text": "Change",
                    "visuallyHiddenText": "mammogram item 2",
                    "classes": "nhsuk-link--no-visited-state",
                },
                "reason_for_continuing": "A reason",
            },
        ]

    @time_machine.travel(datetime(2026, 3, 24, tzinfo=tz.utc))
    def test_last_confirmed_mammogram(self, user):
        confirmed_mammogram = ConfirmedPreviousMammogram(
            location_details="Somewhere",
            exact_date=date(2022, 1, 1),
        )

        result = LastKnownMammogramPresenter(
            user=user,
            reported_mammograms=[],
            last_confirmed_mammogram=confirmed_mammogram,
            appointment_pk=uuid4(),
            current_url="/mammograms/abc",
        )

        assert result.last_confirmed_mammogram == {
            "date": {
                "absolute": "1 January 2022",
                "relative": "4 years, 2 months ago",
            },
            "location": "Somewhere",
        }

    def test_last_confirmed_mammogram_none(self, user):
        result = LastKnownMammogramPresenter(
            user=user,
            reported_mammograms=[],
            last_confirmed_mammogram=None,
            appointment_pk=uuid4(),
            current_url="/mammograms/abc",
        )

        assert result.last_confirmed_mammogram is None

    def test_add_link(self, user, reported_today):
        appointment_pk = uuid4()
        current_url = "/mammograms/abc"

        result = LastKnownMammogramPresenter(
            user=user,
            reported_mammograms=[reported_today],
            last_confirmed_mammogram=None,
            appointment_pk=appointment_pk,
            current_url=current_url,
        )

        assert result.add_link == {
            "href": f"/mammograms/{appointment_pk}/previous-mammograms/add?return_url={current_url}",
            "text": "Add another",
            "visuallyHiddenText": "mammogram",
        }
