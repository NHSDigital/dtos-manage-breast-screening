from datetime import date, datetime
from datetime import timezone as tz
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from manage_breast_screening.participants.presenters import (
    ParticipantAppointmentsPresenter,
    ParticipantPresenter,
)

from ..models import Appointment, AppointmentStatus
from .factories import ParticipantAddressFactory, ParticipantFactory


class TestParticipantPresenter:
    @pytest.fixture(autouse=True)
    def set_time(self, time_machine):
        time_machine.move_to(datetime(2025, 1, 1, tzinfo=tz.utc))

    @pytest.fixture
    def participant(self):
        participant_id = uuid4()
        participant = ParticipantFactory.build(
            pk=participant_id,
            nhs_number="99900900829",
            ethnic_background_id="irish",
            first_name="Firstname",
            last_name="Lastname",
            gender="Female",
            email="Firstname.Lastname@example.com",
            phone="07700 900000",
            date_of_birth=date(1955, 1, 1),
            risk_level=None,
            extra_needs=None,
        )
        participant.address = ParticipantAddressFactory.build(
            participant=participant, lines=["1", "2", "3"], postcode="A123 "
        )

        return participant

    def test_presented_values(self, participant):
        result = ParticipantPresenter(participant)

        assert result.extra_needs is None
        assert result.ethnic_background == "Irish"
        assert result.ethnic_category == "White"
        assert result.full_name == "Firstname Lastname"
        assert result.gender == "Female"
        assert result.email == "Firstname.Lastname@example.com"
        assert result.address == {"lines": ["1", "2", "3"], "postcode": "A123 "}
        assert result.phone == "07700 900000"
        assert result.nhs_number == "999 009 00829"
        assert result.date_of_birth == "1 January 1955"
        assert result.age == "70 years"
        assert result.risk_level == ""
        assert result.url == f"/participants/{participant.pk}/"

    @pytest.mark.parametrize(
        "background_id,expected_display",
        [
            (None, None),
            ("caribbean", "Caribbean"),
            ("any_other_white_background", "any other White background"),
            (
                "any_other_mixed_or_multiple_ethnic_background",
                "any other mixed or multiple ethnic background",
            ),
            ("any_other_asian_background", "any other Asian background"),
            (
                "any_other_black_african_or_caribbean_background",
                "any other Black, African or Caribbean background",
            ),
            ("any_other_ethnic_background", "any other ethnic group"),
        ],
    )
    def test_ethnic_background(self, participant, background_id, expected_display):
        participant.ethnic_background_id = background_id
        result = ParticipantPresenter(participant)

        assert result.ethnic_background == expected_display

    def test_ethnicity_not_shared(self, participant):
        assert not ParticipantPresenter(participant).ethnicity_not_shared

        participant.ethnic_background_id = "prefer_not_to_say"

        assert ParticipantPresenter(participant).ethnicity_not_shared

    @pytest.mark.parametrize(
        "return_url,expected_url",
        [
            (None, "/participants/{uuid}/edit-ethnicity"),
            ("", "/participants/{uuid}/edit-ethnicity"),
            (
                "/return/path/",
                "/participants/{uuid}/edit-ethnicity?return_url=/return/path/",
            ),
        ],
    )
    def test_ethnicity_url(self, participant, return_url, expected_url):
        presenter = ParticipantPresenter(participant)
        expected = expected_url.replace("{uuid}", str(participant.pk))

        result = presenter.ethnicity_url(return_url)

        assert result == expected

    def test_ethnicity_actions_is_none(self, participant):
        participant.ethnic_background_id = None
        presenter = ParticipantPresenter(participant)
        assert presenter.ethnicity_actions(return_url="/return") is None

    def test_ethnicity_actions(self, participant):
        participant.ethnic_background_id = "any_other_white_background"
        presenter = ParticipantPresenter(participant)
        assert presenter.ethnicity_actions(return_url="/return") == {
            "items": [
                {
                    "href": f"/participants/{participant.pk}/edit-ethnicity?return_url=/return",
                    "text": "Change",
                    "visuallyHiddenText": "ethnicity",
                },
            ],
        }


class TestParticipantAppointmentPresenter:
    def mock_appointment(self, starts_at, pk, status_name=AppointmentStatus.SCHEDULED):
        appointment = MagicMock(spec=Appointment)
        appointment.clinic_slot.starts_at = starts_at
        appointment.clinic_slot.clinic.get_type_display.return_value = "screening"
        appointment.clinic_slot.clinic.setting.name = "West of London BSS"
        appointment.pk = UUID(pk)
        appointment.current_status = AppointmentStatus(name=status_name)

        return appointment

    @pytest.fixture
    def upcoming_appointments(self):
        return [
            self.mock_appointment(
                starts_at=datetime(2025, 1, 1, 9, tzinfo=tz.utc),
                pk="e3d475a6-c405-44d6-bbd7-bcb5cd4d4996",
            )
        ]

    @pytest.fixture
    def past_appointments(self):
        return [
            self.mock_appointment(
                starts_at=datetime(2023, 1, 1, 9, tzinfo=tz.utc),
                pk="e76163c8-a594-4991-890d-a02097c67a2f",
                status_name=AppointmentStatus.PARTIALLY_SCREENED,
            ),
            self.mock_appointment(
                starts_at=datetime(2019, 1, 1, 9, tzinfo=tz.utc),
                pk="6473a629-e7c4-43ca-87f3-ab9526aab07c",
                status_name=AppointmentStatus.SCREENED,
            ),
        ]

    def test_upcoming(self, upcoming_appointments, past_appointments, time_machine):
        time_machine.move_to(datetime(2025, 1, 1, 9, tzinfo=tz.utc))

        presenter = ParticipantAppointmentsPresenter(
            past_appointments=past_appointments,
            upcoming_appointments=upcoming_appointments,
        )
        assert presenter.upcoming == [
            ParticipantAppointmentsPresenter.PresentedAppointment(
                "1 January 2025",
                "Screening",
                "West of London BSS",
                {
                    "classes": "nhsuk-tag--blue app-u-nowrap",
                    "key": "SCHEDULED",
                    "text": "Scheduled",
                },
                "/mammograms/e3d475a6-c405-44d6-bbd7-bcb5cd4d4996/",
            )
        ]

    def test_past(self, upcoming_appointments, past_appointments, time_machine):
        time_machine.move_to(datetime(2025, 1, 1, 9, tzinfo=tz.utc))

        presenter = ParticipantAppointmentsPresenter(
            past_appointments=past_appointments,
            upcoming_appointments=upcoming_appointments,
        )
        assert presenter.past == [
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
