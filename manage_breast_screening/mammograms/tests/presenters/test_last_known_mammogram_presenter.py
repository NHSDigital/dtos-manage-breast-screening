from datetime import date, datetime
from datetime import timezone as tz
from uuid import uuid4

import pytest
import time_machine

from manage_breast_screening.clinics.models import Provider
from manage_breast_screening.mammograms.presenters import LastKnownMammogramPresenter
from manage_breast_screening.participants.models import ParticipantReportedMammogram


class TestLastKnownMammogramPresenter:
    @pytest.fixture
    def reported_today(self):
        return ParticipantReportedMammogram(
            created_at=datetime(2025, 1, 1),
            location_type=ParticipantReportedMammogram.LocationType.ELSEWHERE_UK,
            location_details="Somewhere",
            exact_date=date(2022, 1, 1),
        )

    @pytest.fixture
    def reported_earlier(self):
        return ParticipantReportedMammogram(
            created_at=datetime(2022, 1, 1),
            provider=Provider(name="West of London BSS"),
            location_type=ParticipantReportedMammogram.LocationType.NHS_BREAST_SCREENING_UNIT,
            approx_date="3 years ago",
            additional_information="Abcd",
            different_name="Janet Williams",
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
        result = LastKnownMammogramPresenter(
            [reported_today],
            appointment_pk=uuid4(),
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
            },
        ]

    @time_machine.travel(datetime(2025, 1, 1, tzinfo=tz.utc))
    def test_last_known_mammograms_multiple(self, reported_today, reported_earlier):
        result = LastKnownMammogramPresenter(
            [reported_today, reported_earlier],
            appointment_pk=uuid4(),
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
            },
            {
                "date_added": "3 years ago",
                "additional_information": "Abcd",
                "date": {
                    "value": "Approximate date: 3 years ago",
                },
                "different_name": "Janet Williams",
                "location": "West of London BSS",
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
