from datetime import date, datetime
from datetime import timezone as tz
from uuid import uuid4

import pytest
import time_machine

from manage_breast_screening.mammograms.presenters import LastKnownMammogramPresenter
from manage_breast_screening.participants.models import ParticipantReportedMammogram


@pytest.mark.django_db
class TestLastKnownMammogramPresenter:
    @pytest.fixture
    def reported_today(self, in_progress_appointment):
        return ParticipantReportedMammogram(
            created_at=datetime(2025, 1, 1),
            appointment=in_progress_appointment,
            location_type=ParticipantReportedMammogram.LocationType.ELSEWHERE_UK,
            location_details="Somewhere",
            date_type=ParticipantReportedMammogram.DateType.EXACT,
            exact_date=date(2022, 1, 1),
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
        )

    @time_machine.travel(datetime(2025, 1, 1, tzinfo=tz.utc))
    def test_no_last_known_mammograms(self, reported_today):
        result = LastKnownMammogramPresenter(
            [],
            appointment_pk=uuid4(),
            current_url="/mammograms/abc",
        )

        assert result.last_known_mammograms == []

    @time_machine.travel(datetime(2025, 1, 1, tzinfo=tz.utc))
    def test_last_known_mammograms_single(self, reported_today):
        appointment_pk = uuid4()
        result = LastKnownMammogramPresenter(
            [reported_today],
            appointment_pk=appointment_pk,
            current_url="/mammograms/abc",
        )

        assert result.last_known_mammograms == [
            {
                "date_added": "today",
                "additional_information": "",
                "date": {
                    "absolute": "1 January 2022",
                    "relative": "3 years ago",
                    "is_exact": True,
                },
                "different_name": "",
                "location": "In the UK: Somewhere",
                "change_link": {
                    "href": f"/mammograms/{appointment_pk}/previous-mammograms/{reported_today.pk}?return_url=/mammograms/abc",
                    "text": "Change",
                    "visually_hidden_text": " mammogram item",
                },
                "reason_for_continuing": "",
            },
        ]

    @time_machine.travel(datetime(2025, 1, 1, tzinfo=tz.utc))
    def test_last_known_mammograms_another_nhs_unit(self, in_progress_appointment):
        appointment_pk = uuid4()
        mammogram = ParticipantReportedMammogram(
            created_at=datetime(2025, 1, 1),
            appointment=in_progress_appointment,
            location_type=ParticipantReportedMammogram.LocationType.ANOTHER_NHS_PROVIDER,
            location_details="Old provider",
            date_type=ParticipantReportedMammogram.DateType.EXACT,
            exact_date=date(2022, 1, 1),
        )
        result = LastKnownMammogramPresenter(
            [mammogram],
            appointment_pk=appointment_pk,
            current_url="/mammograms/abc",
        )

        assert result.last_known_mammograms == [
            {
                "date_added": "today",
                "additional_information": "",
                "date": {
                    "absolute": "1 January 2022",
                    "relative": "3 years ago",
                    "is_exact": True,
                },
                "different_name": "",
                "location": "Another NHS breast screening unit: Old provider",
                "change_link": {
                    "href": f"/mammograms/{appointment_pk}/previous-mammograms/{mammogram.pk}?return_url=/mammograms/abc",
                    "text": "Change",
                    "visually_hidden_text": " mammogram item",
                },
                "reason_for_continuing": "",
            },
        ]

    @time_machine.travel(datetime(2025, 1, 1, tzinfo=tz.utc))
    def test_last_known_mammograms_multiple(
        self, in_progress_appointment, reported_today, reported_earlier
    ):
        appointment_pk = uuid4()
        result = LastKnownMammogramPresenter(
            [reported_today, reported_earlier],
            appointment_pk=appointment_pk,
            current_url="/mammograms/abc",
        )

        assert result.last_known_mammograms == [
            {
                "date_added": "today",
                "additional_information": "",
                "date": {
                    "absolute": "1 January 2022",
                    "relative": "3 years ago",
                    "is_exact": True,
                },
                "different_name": "",
                "location": "In the UK: Somewhere",
                "change_link": {
                    "href": f"/mammograms/{appointment_pk}/previous-mammograms/{reported_today.pk}?return_url=/mammograms/abc",
                    "text": "Change",
                    "visually_hidden_text": " mammogram item 1",
                },
                "reason_for_continuing": "",
            },
            {
                "date_added": "3 years ago",
                "additional_information": "Abcd",
                "date": {
                    "value": "Taken 6 months or more ago: 3 years ago",
                },
                "different_name": "Janet Williams",
                "location": in_progress_appointment.provider.name,
                "change_link": {
                    "href": f"/mammograms/{appointment_pk}/previous-mammograms/{reported_earlier.pk}?return_url=/mammograms/abc",
                    "text": "Change",
                    "visually_hidden_text": " mammogram item 2",
                },
                "reason_for_continuing": "A reason",
            },
        ]

    def test_add_link(self, reported_today):
        appointment_pk = uuid4()
        current_url = "/mammograms/abc"

        result = LastKnownMammogramPresenter(
            [reported_today],
            appointment_pk=appointment_pk,
            current_url=current_url,
        )

        assert result.add_link == {
            "href": f"/mammograms/{appointment_pk}/previous-mammograms/add?return_url={current_url}",
            "text": "Add another",
            "visually_hidden_text": "mammogram",
        }
