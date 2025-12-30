from datetime import date, datetime
from datetime import timezone as tz
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
import time_machine

from manage_breast_screening.auth.models import Permission
from manage_breast_screening.clinics.models import ClinicSlot
from manage_breast_screening.mammograms.presenters import (
    AppointmentPresenter,
    ClinicSlotPresenter,
    SpecialAppointmentPresenter,
)
from manage_breast_screening.participants.models import Appointment, AppointmentStatus
from manage_breast_screening.users.models import User


class TestAppointmentPresenter:
    @pytest.fixture
    def mock_appointment(self):
        mock = MagicMock(spec=Appointment)
        mock.screening_episode.participant.nhs_number = "99900900829"
        mock.screening_episode.participant.pk = uuid4()
        return mock

    @pytest.fixture
    def mock_user(self):
        return MagicMock(spec=User)

    @pytest.mark.parametrize(
        "status, expected_classes, expected_text, expected_key, expected_is_confirmed, expected_is_screened",
        [
            (
                AppointmentStatus.CONFIRMED,
                "nhsuk-tag--blue app-u-nowrap",
                "Confirmed",
                "CONFIRMED",
                True,
                False,
            ),
            (
                AppointmentStatus.CHECKED_IN,
                "app-u-nowrap",
                "Checked in",
                "CHECKED_IN",
                False,
                False,
            ),
            (
                AppointmentStatus.ATTENDED_NOT_SCREENED,
                "nhsuk-tag--orange app-u-nowrap",
                "Attended not screened",
                "ATTENDED_NOT_SCREENED",
                False,
                False,
            ),
            (
                AppointmentStatus.SCREENED,
                "nhsuk-tag--green app-u-nowrap",
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
        mock_appointment.current_status = AppointmentStatus(name=status)

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

    @pytest.mark.parametrize(
        "has_permission, status_name, result",
        [
            (True, AppointmentStatus.CONFIRMED, True),
            (True, AppointmentStatus.CHECKED_IN, True),
            (False, AppointmentStatus.CONFIRMED, False),
            (True, AppointmentStatus.IN_PROGRESS, False),
        ],
    )
    def test_can_be_started_by(
        self, mock_appointment, mock_user, has_permission, status_name, result
    ):
        mock_user.has_perm.return_value = has_permission
        mock_appointment.current_status.name = status_name

        assert (
            AppointmentPresenter(mock_appointment).can_be_started_by(mock_user)
            == result
        )

        mock_user.has_perm.assert_called_once_with(
            Permission.START_MAMMOGRAM_APPOINTMENT, mock_appointment
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

    @pytest.mark.parametrize(
        "is_in_progress, is_final_status, expected_result",
        [
            (True, False, "with A. Tester"),
            (False, True, "by A. Tester"),
            (False, False, None),
        ],
    )
    def test_status_attribution(
        self, mock_appointment, is_in_progress, is_final_status, expected_result
    ):
        mock_appointment.current_status.created_by.get_short_name.return_value = (
            "A. Tester"
        )
        mock_appointment.current_status.is_in_progress.return_value = is_in_progress
        mock_appointment.current_status.is_final_status.return_value = is_final_status
        presenter = AppointmentPresenter(mock_appointment)
        assert presenter.status_attribution == expected_result


class TestStatusBarPresenter:
    @pytest.fixture
    def mock_appointment(self):
        mock = MagicMock(spec=Appointment)
        mock.screening_episode.participant.nhs_number = "99900900829"
        mock.screening_episode.participant.pk = uuid4()
        return mock

    @pytest.fixture
    def mock_user(self):
        return MagicMock(spec=User)

    def test_show_status_bar_when_in_progress_and_user_is_owner(
        self, mock_appointment, mock_user
    ):
        mock_appointment.current_status.name = AppointmentStatus.IN_PROGRESS
        mock_user.nhs_uid = "user-123"
        mock_appointment.current_status.created_by.nhs_uid = "user-123"
        presenter = AppointmentPresenter(mock_appointment)
        assert presenter.status_bar.show_status_bar_for(mock_user)

    def test_show_status_bar_when_user_is_not_owner(self, mock_appointment, mock_user):
        mock_appointment.current_status.name = AppointmentStatus.IN_PROGRESS
        mock_user.nhs_uid = "user-123"
        mock_appointment.current_status.created_by.nhs_uid = "user-456"
        presenter = AppointmentPresenter(mock_appointment)
        assert not presenter.status_bar.show_status_bar_for(mock_user)

    @pytest.mark.parametrize(
        "current_status",
        [
            AppointmentStatus.CONFIRMED,
            AppointmentStatus.CHECKED_IN,
            AppointmentStatus.DID_NOT_ATTEND,
            AppointmentStatus.SCREENED,
            AppointmentStatus.PARTIALLY_SCREENED,
            AppointmentStatus.ATTENDED_NOT_SCREENED,
        ],
    )
    def test_dont_show_status_bar_when_not_in_progress(
        self, mock_appointment, mock_user, current_status
    ):
        mock_appointment.current_status.name = current_status
        mock_user.nhs_uid = "user-123"
        mock_appointment.current_status.created_by.nhs_uid = "user-123"
        presenter = AppointmentPresenter(mock_appointment)
        assert not presenter.status_bar.show_status_bar_for(mock_user)

    def test_tag_properties(self, mock_appointment):
        presenter = AppointmentPresenter(mock_appointment)
        assert presenter.status_bar.tag_properties == {
            "classes": "nhsuk-tag--yellow nhsuk-u-margin-left-1",
            "text": "Special appointment",
        }

    def test_attributes(self, mock_appointment):
        presenter = AppointmentPresenter(mock_appointment)
        assert presenter.status_bar.appointment == presenter
        assert presenter.status_bar.clinic_slot == presenter.clinic_slot
        assert presenter.status_bar.participant == presenter.participant


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

    @time_machine.travel(datetime(2025, 5, 19, tzinfo=tz.utc))
    def test_clinic_date_and_slot_time(self, clinic_slot_mock):
        clinic_slot_mock.starts_at = datetime(2025, 1, 2, 9, 30)
        clinic_slot_mock.duration_in_minutes = 30
        clinic_slot_mock.clinic.starts_at = date(2025, 1, 2)

        assert (
            ClinicSlotPresenter(clinic_slot_mock).clinic_date_and_slot_time
            == "2 January 2025 at 9:30am"
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
