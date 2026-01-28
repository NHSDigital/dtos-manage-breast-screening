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
from manage_breast_screening.participants.models.appointment import (
    AppointmentStatusNames,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentStatusFactory,
)
from manage_breast_screening.users.models import User


class TestAppointmentPresenter:
    @pytest.fixture
    def mock_appointment(self):
        mock = MagicMock(spec=Appointment)
        mock.pk = "53ce8d3b-9e65-471a-b906-73809c0475d0"
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
                AppointmentStatusNames.SCHEDULED,
                "nhsuk-tag--blue app-u-nowrap",
                "Scheduled",
                "SCHEDULED",
                True,
                False,
            ),
            (
                AppointmentStatusNames.CHECKED_IN,
                "app-u-nowrap",
                "Checked in",
                "CHECKED_IN",
                False,
                False,
            ),
            (
                AppointmentStatusNames.ATTENDED_NOT_SCREENED,
                "nhsuk-tag--orange app-u-nowrap",
                "Attended not screened",
                "ATTENDED_NOT_SCREENED",
                False,
                False,
            ),
            (
                AppointmentStatusNames.SCREENED,
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
            (True, AppointmentStatusNames.SCHEDULED, True),
            (True, AppointmentStatusNames.CHECKED_IN, True),
            (False, AppointmentStatusNames.SCHEDULED, False),
            (True, AppointmentStatusNames.IN_PROGRESS, False),
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
            Permission.DO_MAMMOGRAM_APPOINTMENT, mock_appointment
        )

    @pytest.mark.parametrize(
        "has_permission, status_name, result",
        [
            (True, AppointmentStatusNames.PAUSED, True),
            (False, AppointmentStatusNames.PAUSED, False),
            (True, AppointmentStatusNames.SCREENED, False),
        ],
    )
    def test_can_be_resumed(
        self, mock_appointment, mock_user, has_permission, status_name, result
    ):
        mock_user.has_perm.return_value = has_permission
        mock_appointment.current_status.name = status_name
        mock_appointment.current_status.is_in_progress_with.return_value = False

        assert (
            AppointmentPresenter(mock_appointment).can_be_resumed_by(mock_user)
            == result
        )

        mock_user.has_perm.assert_called_once_with(
            Permission.DO_MAMMOGRAM_APPOINTMENT, mock_appointment
        )

    def test_can_be_resumed_by_the_same_user_when_in_progress(
        self, mock_appointment, mock_user
    ):
        mock_user.has_perm.return_value = True
        mock_appointment.current_status.name = AppointmentStatusNames.PAUSED
        mock_appointment.current_status.is_in_progress_with.return_value = True

        assert AppointmentPresenter(mock_appointment).can_be_resumed_by(mock_user)

        mock_user.has_perm.assert_called_once_with(
            Permission.DO_MAMMOGRAM_APPOINTMENT, mock_appointment
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

    class TestCurrentStatus:
        @pytest.mark.parametrize(
            "status_name, expected_classes, expected_text, expected_key, is_confirmed, is_screened",
            [
                (
                    AppointmentStatusNames.CHECKED_IN,
                    "app-u-nowrap",
                    "Checked in",
                    "CHECKED_IN",
                    False,
                    False,
                ),
                (
                    AppointmentStatusNames.SCHEDULED,
                    "nhsuk-tag--blue app-u-nowrap",
                    "Scheduled",
                    "SCHEDULED",
                    True,
                    False,
                ),
                (
                    AppointmentStatusNames.IN_PROGRESS,
                    "nhsuk-tag--aqua-green app-u-nowrap",
                    "In progress",
                    "IN_PROGRESS",
                    False,
                    False,
                ),
                (
                    AppointmentStatusNames.CANCELLED,
                    "nhsuk-tag--red app-u-nowrap",
                    "Cancelled",
                    "CANCELLED",
                    False,
                    False,
                ),
                (
                    AppointmentStatusNames.DID_NOT_ATTEND,
                    "nhsuk-tag--red app-u-nowrap",
                    "Did not attend",
                    "DID_NOT_ATTEND",
                    False,
                    False,
                ),
                (
                    AppointmentStatusNames.SCREENED,
                    "nhsuk-tag--green app-u-nowrap",
                    "Screened",
                    "SCREENED",
                    False,
                    True,
                ),
                (
                    AppointmentStatusNames.PARTIALLY_SCREENED,
                    "nhsuk-tag--orange app-u-nowrap",
                    "Partially screened",
                    "PARTIALLY_SCREENED",
                    False,
                    False,
                ),
                (
                    AppointmentStatusNames.ATTENDED_NOT_SCREENED,
                    "nhsuk-tag--orange app-u-nowrap",
                    "Attended not screened",
                    "ATTENDED_NOT_SCREENED",
                    False,
                    False,
                ),
            ],
        )
        def test_current_status_properties(
            self,
            mock_appointment,
            status_name,
            expected_classes,
            expected_text,
            expected_key,
            is_confirmed,
            is_screened,
        ):
            mock_appointment.current_status = AppointmentStatusFactory.build(
                name=status_name
            )
            presenter = AppointmentPresenter(mock_appointment)

            expected = {
                "classes": expected_classes,
                "text": expected_text,
                "key": expected_key,
                "is_confirmed": is_confirmed,
                "is_screened": is_screened,
            }
            assert presenter.current_status == expected

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

    def test_workflow_steps_confirm_identity(self, mock_appointment):
        mock_appointment.completed_workflow_steps = MagicMock()
        mock_appointment.completed_workflow_steps.values_list.return_value = []

        steps = AppointmentPresenter(mock_appointment).workflow_steps(
            "CONFIRM_IDENTITY"
        )

        assert steps == [
            {
                "label": "Confirm identity",
                "completed": False,
                "current": True,
                "disabled": False,
                "classes": "app-workflow-side-nav__item app-workflow-side-nav__item--current",
                "url": "/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/confirm-identity/",
            },
            {
                "label": "Review medical information",
                "completed": False,
                "current": False,
                "disabled": True,
                "classes": "app-workflow-side-nav__item app-workflow-side-nav__item--disabled",
                "url": "/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/record-medical-information/",
            },
            {
                "label": "Take images",
                "completed": False,
                "current": False,
                "disabled": True,
                "classes": "app-workflow-side-nav__item app-workflow-side-nav__item--disabled",
                "url": "/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/take-images/",
            },
            {
                "label": "Check information",
                "completed": False,
                "current": False,
                "disabled": True,
                "classes": "app-workflow-side-nav__item app-workflow-side-nav__item--disabled",
                "url": "/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/check-information/",
            },
        ]

    def test_workflow_steps_review_medical_information(self, mock_appointment):
        mock_appointment.completed_workflow_steps = MagicMock()
        mock_appointment.completed_workflow_steps.values_list.return_value = [
            "CONFIRM_IDENTITY"
        ]

        steps = AppointmentPresenter(mock_appointment).workflow_steps(
            "REVIEW_MEDICAL_INFORMATION"
        )
        assert steps == [
            {
                "label": "Confirm identity",
                "completed": True,
                "current": False,
                "disabled": False,
                "classes": "app-workflow-side-nav__item app-workflow-side-nav__item--completed",
                "url": "/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/confirm-identity/",
            },
            {
                "label": "Review medical information",
                "completed": False,
                "current": True,
                "disabled": False,
                "classes": "app-workflow-side-nav__item app-workflow-side-nav__item--current",
                "url": "/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/record-medical-information/",
            },
            {
                "label": "Take images",
                "completed": False,
                "current": False,
                "disabled": True,
                "classes": "app-workflow-side-nav__item app-workflow-side-nav__item--disabled",
                "url": "/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/take-images/",
            },
            {
                "label": "Check information",
                "completed": False,
                "current": False,
                "disabled": True,
                "classes": "app-workflow-side-nav__item app-workflow-side-nav__item--disabled",
                "url": "/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/check-information/",
            },
        ]

    def test_workflow_steps_take_images(self, mock_appointment):
        mock_appointment.completed_workflow_steps = MagicMock()
        mock_appointment.completed_workflow_steps.values_list.return_value = [
            "CONFIRM_IDENTITY",
            "REVIEW_MEDICAL_INFORMATION",
        ]

        steps = AppointmentPresenter(mock_appointment).workflow_steps("TAKE_IMAGES")
        assert steps == [
            {
                "label": "Confirm identity",
                "completed": True,
                "current": False,
                "disabled": False,
                "classes": "app-workflow-side-nav__item app-workflow-side-nav__item--completed",
                "url": "/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/confirm-identity/",
            },
            {
                "label": "Review medical information",
                "completed": True,
                "current": False,
                "disabled": False,
                "classes": "app-workflow-side-nav__item app-workflow-side-nav__item--completed",
                "url": "/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/record-medical-information/",
            },
            {
                "label": "Take images",
                "completed": False,
                "current": True,
                "disabled": False,
                "classes": "app-workflow-side-nav__item app-workflow-side-nav__item--current",
                "url": "/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/take-images/",
            },
            {
                "label": "Check information",
                "completed": False,
                "current": False,
                "disabled": True,
                "classes": "app-workflow-side-nav__item app-workflow-side-nav__item--disabled",
                "url": "/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/check-information/",
            },
        ]

    def test_workflow_steps_check_information(self, mock_appointment):
        mock_appointment.completed_workflow_steps = MagicMock()
        mock_appointment.completed_workflow_steps.values_list.return_value = [
            "CONFIRM_IDENTITY",
            "REVIEW_MEDICAL_INFORMATION",
            "TAKE_IMAGES",
        ]

        steps = AppointmentPresenter(mock_appointment).workflow_steps(
            "CHECK_INFORMATION"
        )
        assert steps == [
            {
                "label": "Confirm identity",
                "completed": True,
                "current": False,
                "disabled": False,
                "classes": "app-workflow-side-nav__item app-workflow-side-nav__item--completed",
                "url": "/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/confirm-identity/",
            },
            {
                "label": "Review medical information",
                "completed": True,
                "current": False,
                "disabled": False,
                "classes": "app-workflow-side-nav__item app-workflow-side-nav__item--completed",
                "url": "/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/record-medical-information/",
            },
            {
                "label": "Take images",
                "completed": True,
                "current": False,
                "disabled": False,
                "classes": "app-workflow-side-nav__item app-workflow-side-nav__item--completed",
                "url": "/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/take-images/",
            },
            {
                "label": "Check information",
                "completed": False,
                "current": True,
                "disabled": False,
                "classes": "app-workflow-side-nav__item app-workflow-side-nav__item--current",
                "url": "/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/check-information/",
            },
        ]

    def test_workflow_steps_on_review_medical_information_when_already_reviewed(
        self, mock_appointment
    ):
        mock_appointment.completed_workflow_steps = MagicMock()
        mock_appointment.completed_workflow_steps.values_list.return_value = [
            "CONFIRM_IDENTITY",
            "REVIEW_MEDICAL_INFORMATION",
        ]

        steps = AppointmentPresenter(mock_appointment).workflow_steps(
            "REVIEW_MEDICAL_INFORMATION"
        )

        assert steps == [
            {
                "label": "Confirm identity",
                "completed": True,
                "current": False,
                "disabled": False,
                "classes": "app-workflow-side-nav__item app-workflow-side-nav__item--completed",
                "url": "/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/confirm-identity/",
            },
            {
                "label": "Review medical information",
                "completed": True,
                "current": True,
                "disabled": False,
                "classes": "app-workflow-side-nav__item app-workflow-side-nav__item--current app-workflow-side-nav__item--completed",
                "url": "/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/record-medical-information/",
            },
            {
                "label": "Take images",
                "completed": False,
                "current": False,
                "disabled": False,
                "classes": "app-workflow-side-nav__item",
                "url": "/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/take-images/",
            },
            {
                "label": "Check information",
                "completed": False,
                "current": False,
                "disabled": True,
                "classes": "app-workflow-side-nav__item app-workflow-side-nav__item--disabled",
                "url": "/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/check-information/",
            },
        ]

    def test_workflow_steps_on_confirm_identity_when_already_taken_images(
        self, mock_appointment
    ):
        mock_appointment.completed_workflow_steps = MagicMock()
        mock_appointment.completed_workflow_steps.values_list.return_value = [
            "CONFIRM_IDENTITY",
            "REVIEW_MEDICAL_INFORMATION",
            "TAKE_IMAGES",
        ]

        steps = AppointmentPresenter(mock_appointment).workflow_steps(
            "CONFIRM_IDENTITY"
        )
        assert steps == [
            {
                "label": "Confirm identity",
                "completed": True,
                "current": True,
                "disabled": False,
                "classes": "app-workflow-side-nav__item app-workflow-side-nav__item--current app-workflow-side-nav__item--completed",
                "url": "/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/confirm-identity/",
            },
            {
                "label": "Review medical information",
                "completed": True,
                "current": False,
                "disabled": False,
                "classes": "app-workflow-side-nav__item app-workflow-side-nav__item--completed",
                "url": "/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/record-medical-information/",
            },
            {
                "label": "Take images",
                "completed": True,
                "current": False,
                "disabled": False,
                "classes": "app-workflow-side-nav__item app-workflow-side-nav__item--completed",
                "url": "/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/take-images/",
            },
            {
                "label": "Check information",
                "completed": False,
                "current": False,
                "disabled": False,
                "classes": "app-workflow-side-nav__item",
                "url": "/mammograms/53ce8d3b-9e65-471a-b906-73809c0475d0/check-information/",
            },
        ]


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
        mock_appointment.current_status.is_in_progress.return_value = True
        mock_user.nhs_uid = "user-123"
        mock_appointment.current_status.created_by.nhs_uid = "user-123"
        presenter = AppointmentPresenter(mock_appointment)
        assert presenter.status_bar.show_status_bar_for(mock_user)

    def test_dont_show_status_bar_when_user_is_not_owner(
        self, mock_appointment, mock_user
    ):
        mock_appointment.current_status.is_in_progress.return_value = True
        mock_user.nhs_uid = "user-123"
        mock_appointment.current_status.created_by.nhs_uid = "user-456"
        presenter = AppointmentPresenter(mock_appointment)
        assert not presenter.status_bar.show_status_bar_for(mock_user)

    def test_dont_show_status_bar_when_not_in_progress(
        self, mock_appointment, mock_user
    ):
        mock_appointment.current_status.is_in_progress.return_value = False
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
