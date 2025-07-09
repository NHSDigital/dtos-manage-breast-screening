from datetime import date, datetime
from datetime import timezone as tz
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
import time_machine

from manage_breast_screening.clinics.models import ClinicSlot
from manage_breast_screening.participants.models import (
    Appointment,
    AppointmentStatus,
    ScreeningEpisode,
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
    @pytest.fixture()
    def mock_screening(self):
        mock_screening = MagicMock(spec=ScreeningEpisode)
        mock_screening.created_at = datetime(2015, 1, 1)
        return mock_screening

    @time_machine.travel(datetime(2025, 1, 1, tzinfo=tz.utc))
    def test_last_known_mammogram(self, mock_screening):
        result = LastKnownMammogramPresenter(
            mock_screening,
            participant_pk=uuid4(),
            current_url="/mammograms/start-screening/abc",
        )

        assert result.last_known_mammogram == {
            "date": "1 January 2015",
            "relative_date": "10 years ago",
            "location": None,
            "type": None,
        }

    def test_add_link(self, mock_screening):
        participant_id = uuid4()
        current_url = "/mammograms/start-screening/abc"

        result = LastKnownMammogramPresenter(
            mock_screening,
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

    @time_machine.travel(datetime(2025, 5, 19, tzinfo=tz.utc))
    def test_slot_time_and_clinic_date(self, clinic_slot_mock):
        clinic_slot_mock.starts_at = datetime(2025, 1, 2, 9, 30)
        clinic_slot_mock.duration_in_minutes = 30
        clinic_slot_mock.clinic.starts_at = date(2025, 1, 2)

        assert (
            ClinicSlotPresenter(clinic_slot_mock).slot_time_and_clinic_date
            == "9:30am (30 minutes) - 2 January 2025 (4 months, 17 days ago)"
        )
