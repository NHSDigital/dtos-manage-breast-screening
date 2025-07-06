from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

from django.urls import reverse

from ..core.utils.date_formatting import format_date, format_relative_date
from ..core.utils.string_formatting import (
    format_age,
    format_nhs_number,
    format_phone_number,
    sentence_case,
)
from .models import AppointmentStatus


def status_colour(status):
    """
    Color to render the status tag
    """
    match status:
        case AppointmentStatus.CHECKED_IN:
            return ""  # no colour will get solid dark blue
        case AppointmentStatus.SCREENED:
            return "green"
        case AppointmentStatus.DID_NOT_ATTEND | AppointmentStatus.CANCELLED:
            return "red"
        case (
            AppointmentStatus.ATTENDED_NOT_SCREENED
            | AppointmentStatus.PARTIALLY_SCREENED
        ):
            return "orange"
        case _:
            return "blue"  # default blue


class ParticipantPresenter:
    def __init__(self, participant):
        self._participant = participant

        self.pk = participant.pk
        self.extra_needs = participant.extra_needs
        self.ethnic_category = participant.ethnic_category
        self.full_name = participant.full_name
        self.gender = participant.gender
        self.email = participant.email
        self.phone = format_phone_number(participant.phone)
        self.nhs_number = format_nhs_number(participant.nhs_number)
        self.date_of_birth = format_date(participant.date_of_birth)
        self.age = format_age(participant.age())
        self.risk_level = sentence_case(participant.risk_level)
        self.url = reverse("participants:show", kwargs={"pk": participant.pk})

    def ethnicity_url(self, return_url):
        url = reverse(
            "participants:edit_ethnicity", kwargs={"pk": self._participant.pk}
        )
        if return_url:
            url += "?return_url=" + quote(return_url)
        return url

    @property
    def address(self):
        address = self._participant.address
        if not address:
            return {}

        return {"lines": address.lines, "postcode": address.postcode}

    @property
    def ethnic_background(self):
        background = self._participant.ethnic_background

        if background and background.startswith("Any other"):
            return background[0].lower() + background[1:]

        return background


class ScreeningHistoryPresenter:
    def __init__(self, screening_episodes):
        self._episodes = list(screening_episodes)
        self._last_known_screening = screening_episodes[1]

    @property
    def last_known_screening(self):
        return (
            {
                "date": format_date(self._last_known_screening.created_at),
                "relative_date": format_relative_date(
                    self._last_known_screening.created_at
                ),
                # TODO: the current model doesn't allow for knowing the type and location of a historical screening
                # if it is not tied to one of our clinic slots.
                "location": None,
                "type": None,
            }
            if self._last_known_screening
            else {}
        )


class ParticipantAppointmentsPresenter:
    @dataclass
    class PresentedAppointment:
        starts_at: str
        clinic_type: str
        setting_name: str
        status: dict[str, Any]
        url: str

    def __init__(self, past_appointments, upcoming_appointments):
        self.past = [
            self._present_appointment(appointment) for appointment in past_appointments
        ]
        self.upcoming = [
            self._present_appointment(appointment)
            for appointment in upcoming_appointments
        ]

    def _present_appointment(self, appointment):
        clinic_slot = appointment.clinic_slot
        clinic = clinic_slot.clinic
        setting = clinic.setting

        return self.PresentedAppointment(
            starts_at=format_date(clinic_slot.starts_at),
            clinic_type=clinic.get_type_display().capitalize(),
            setting_name=sentence_case(setting.name),
            status=self._present_status(appointment),
            url=reverse("mammograms:start_screening", kwargs={"pk": appointment.pk}),
        )

    def _present_status(self, appointment):
        current_status = appointment.current_status
        colour = status_colour(current_status.state)

        return {
            "classes": f"nhsuk-tag--{colour} app-nowrap" if colour else "app-nowrap",
            "text": current_status.get_state_display(),
            "key": current_status.state,
        }
