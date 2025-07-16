from datetime import date, datetime
from datetime import timezone as tz
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
import time_machine

from manage_breast_screening.clinics.models import ClinicSlot, Provider
from manage_breast_screening.participants.models import (
    Appointment,
    AppointmentStatus,
    ParticipantReportedMammogram,
)

from ..presenters import (
    AppointmentPresenter,
    ClinicSlotPresenter,
    LastKnownMammogramPresenter,
)


class TestAppointmentPresenter:
    @pytest.fixture
    def mock_appointment(self):
        mock = MagicMock(spec=Appointment)
        mock.screening_episode.participant.nhs_number = "99900900829"
        mock.screening_episode.participant.pk = uuid4()
        return mock

    @pytest.mark.parametrize(
        "status, expected_classes, expected_text, expected_key, expected_is_confirmed",
        [
            (
                AppointmentStatus.CONFIRMED,
                "nhsuk-tag--blue app-nowrap",
                "Confirmed",
                "CONFIRMED",
                True,
            ),
            (
                AppointmentStatus.CHECKED_IN,
                "app-nowrap",
                "Checked in",
                "CHECKED_IN",
                False,
            ),
            (
                AppointmentStatus.ATTENDED_NOT_SCREENED,
                "nhsuk-tag--orange app-nowrap",
                "Attended not screened",
                "ATTENDED_NOT_SCREENED",
                False,
            ),
        ],
    )
    def test_status(
        self,
        mock_appointment,
        status,
        expected_classes,
        expected_text,
        expected_key,
        expected_is_confirmed,
    ):
        mock_appointment.current_status = AppointmentStatus(state=status)

        result = AppointmentPresenter(mock_appointment).current_status

        assert result["classes"] == expected_classes
        assert result["text"] == expected_text
        assert result["key"] == expected_key
        assert result["is_confirmed"] == expected_is_confirmed

    def test_clinic_url(self, mock_appointment):
        mock_appointment.clinic_slot.clinic.pk = "ef742f9d-76fb-47f1-8292-f7dcf456fc71"
        assert (
            AppointmentPresenter(mock_appointment).clinic_url
            == "/clinics/ef742f9d-76fb-47f1-8292-f7dcf456fc71/"
        )

    def test_participant_url(self, mock_appointment):
        mock_appointment.screening_episode.participant.pk = UUID(
            "ac1b68ec-06a4-40a0-a016-7108dffe4397"
        )
        result = AppointmentPresenter(mock_appointment)
        assert (
            result.participant_url
            == "/participants/ac1b68ec-06a4-40a0-a016-7108dffe4397/"
        )

    def test_screening_protocol(self, mock_appointment):
        mock_appointment.screening_episode.get_protocol_display.return_value = (
            "Family history"
        )

        result = AppointmentPresenter(mock_appointment)

        assert result.screening_protocol == "Family history"

    @pytest.mark.parametrize(
        "extra_needs, expected_result",
        [
            ([], False),
            (["Wheelchair access"], True),
            (["Wheelchair access", "Interpreter required"], True),
        ],
    )
    def test_is_special_appointment(
        self, mock_appointment, extra_needs, expected_result
    ):
        mock_appointment.screening_episode.participant.extra_needs = extra_needs
        presenter = AppointmentPresenter(mock_appointment)
        assert presenter.is_special_appointment == expected_result


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
            participant_pk=uuid4(),
            current_url="/mammograms/abc",
        )

        assert result.last_known_mammograms == []

    @time_machine.travel(datetime(2025, 1, 1, tzinfo=tz.utc))
    def test_last_known_mammograms_single(self, reported_today):
        result = LastKnownMammogramPresenter(
            [reported_today],
            participant_pk=uuid4(),
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
            participant_pk=uuid4(),
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
        participant_id = uuid4()
        current_url = "/mammograms/abc"

        result = LastKnownMammogramPresenter(
            [reported_today],
            participant_pk=participant_id,
            current_url=current_url,
        )

        assert result.add_link == {
            "href": f"/participants/{participant_id}/previous-mammograms/add?return_url={current_url}",
            "text": "Add another",
            "visually_hidden_text": "mammogram",
        }


class TestClinicSlotPresenter:
    @pytest.fixture
    def clinic_slot_mock(self):
        mock = MagicMock(spec=ClinicSlot)
        return mock

    def test_clinic_type(self, clinic_slot_mock):
        clinic_slot_mock.clinic.get_type_display.return_value = "Screening"

        assert ClinicSlotPresenter(clinic_slot_mock).clinic_type == "Screening"

    def test_clinic_url(self, clinic_slot_mock):
        clinic_slot_mock.clinic.pk = "ef742f9d-76fb-47f1-8292-f7dcf456fc71"
        assert (
            ClinicSlotPresenter(clinic_slot_mock).clinic_url
            == "/clinics/ef742f9d-76fb-47f1-8292-f7dcf456fc71/"
        )

    @time_machine.travel(datetime(2025, 5, 19, tzinfo=tz.utc))
    def test_slot_time_and_clinic_date(self, clinic_slot_mock):
        clinic_slot_mock.starts_at = datetime(2025, 1, 2, 9, 30)
        clinic_slot_mock.duration_in_minutes = 30
        clinic_slot_mock.clinic.starts_at = date(2025, 1, 2)

        assert (
            ClinicSlotPresenter(clinic_slot_mock).slot_time_and_clinic_date
            == "9:30am (30 minutes) - 2 January 2025 (4 months, 17 days ago)"
        )
