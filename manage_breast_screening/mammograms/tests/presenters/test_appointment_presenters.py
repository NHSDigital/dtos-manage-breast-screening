from datetime import date, datetime
from datetime import timezone as tz
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
import time_machine

from manage_breast_screening.clinics.models import ClinicSlot
from manage_breast_screening.mammograms.presenters import (
    AppointmentPresenter,
    ClinicSlotPresenter,
    SpecialAppointmentPresenter,
)
from manage_breast_screening.participants.models import Appointment, AppointmentStatus


class TestAppointmentPresenter:
    @pytest.fixture
    def mock_appointment(self):
        mock = MagicMock(spec=Appointment)
        mock.screening_episode.participant.nhs_number = "99900900829"
        mock.screening_episode.participant.pk = uuid4()
        return mock

    @pytest.mark.parametrize(
        "status, expected_classes, expected_text, expected_key, expected_is_confirmed, expected_is_screened",
        [
            (
                AppointmentStatus.CONFIRMED,
                "nhsuk-tag--blue app-nowrap",
                "Confirmed",
                "CONFIRMED",
                True,
                False,
            ),
            (
                AppointmentStatus.CHECKED_IN,
                "app-nowrap",
                "Checked in",
                "CHECKED_IN",
                False,
                False,
            ),
            (
                AppointmentStatus.ATTENDED_NOT_SCREENED,
                "nhsuk-tag--orange app-nowrap",
                "Attended not screened",
                "ATTENDED_NOT_SCREENED",
                False,
                False,
            ),
            (
                AppointmentStatus.SCREENED,
                "nhsuk-tag--green app-nowrap",
                "Screened",
                "SCREENED",
                False,
                True,
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
        expected_is_screened,
    ):
        mock_appointment.current_status = AppointmentStatus(state=status)

        result = AppointmentPresenter(mock_appointment).current_status

        assert result["classes"] == expected_classes
        assert result["text"] == expected_text
        assert result["key"] == expected_key
        assert result["is_confirmed"] == expected_is_confirmed
        assert result["is_screened"] == expected_is_screened

    @pytest.mark.parametrize(
        "extra_needs, active, expected_value",
        [
            ({}, True, True),
            ({}, False, False),
            (
                {"PHYSICAL_RESTRICTION": {}},
                True,
                False,
            ),
        ],
    )
    def test_can_be_made_special(
        self, mock_appointment, extra_needs, active, expected_value
    ):
        mock_appointment.active = active
        mock_appointment.screening_episode.participant.extra_needs = extra_needs
        assert (
            AppointmentPresenter(mock_appointment).can_be_made_special == expected_value
        )

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

    def test_special_appointment_url(self, mock_appointment):
        mock_appointment.pk = "68d758d0-792d-430f-9c52-1e7a0c2aa1dd"
        result = AppointmentPresenter(mock_appointment)
        assert (
            result.special_appointment_url
            == "/mammograms/68d758d0-792d-430f-9c52-1e7a0c2aa1dd/special-appointment/"
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


class TestSpecialAppointmentPresenter:
    def test_change_url(self):
        appointment_pk = "68d758d0-792d-430f-9c52-1e7a0c2aa1dd"
        result = SpecialAppointmentPresenter({}, appointment_pk)
        assert (
            result.change_url
            == "/mammograms/68d758d0-792d-430f-9c52-1e7a0c2aa1dd/special-appointment/"
        )

    def test_reasons(self):
        appointment_pk = "68d758d0-792d-430f-9c52-1e7a0c2aa1dd"
        result = SpecialAppointmentPresenter(
            {
                "PHYSICAL_RESTRICTION": {"details": "broken foot", "temporary": "True"},
                "SOCIAL_EMOTIONAL_MENTAL_HEALTH": {},
            },
            appointment_pk,
        )
        assert result.reasons == [
            {
                "details": "broken foot",
                "label": "Physical restriction",
                "temporary": "True",
            },
            {
                "details": None,
                "label": "Social, emotional, and mental health",
                "temporary": None,
            },
        ]
