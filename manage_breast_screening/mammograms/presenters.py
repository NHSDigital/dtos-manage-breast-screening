from functools import cached_property

from django.urls import reverse

from ..core.utils.date_formatting import format_date, format_relative_date, format_time
from ..participants.models import AppointmentStatus
from ..participants.presenters import ParticipantPresenter, status_colour


def present_secondary_nav(pk):
    """
    Build a secondary nav for reviewing the information of screened/partially screened appointments.
    """
    return [
        {
            "id": "all",
            "text": "Appointment details",
            "href": reverse("mammograms:start_screening", kwargs={"pk": pk}),
            "current": True,
        },
        {"id": "medical_information", "text": "Medical information", "href": "#"},
        {"id": "images", "text": "Images", "href": "#"},
    ]


class AppointmentPresenter:
    def __init__(self, appointment):
        self._appointment = appointment

        self.allStatuses = AppointmentStatus
        self.pk = appointment.pk
        self.clinic_slot = ClinicSlotPresenter(appointment.clinic_slot)
        self.participant = ParticipantPresenter(
            appointment.screening_episode.participant
        )

    @cached_property
    def participant_url(self):
        return self.participant.url

    @cached_property
    def start_time(self):
        return self.clinic_slot.starts_at

    @cached_property
    def current_status(self):
        current_status = self._appointment.current_status

        colour = status_colour(current_status.state)

        return {
            "classes": f"nhsuk-tag--{colour} app-nowrap" if colour else "app-nowrap",
            "text": current_status.get_state_display(),
            "key": current_status.state,
            "is_confirmed": current_status.state == AppointmentStatus.CONFIRMED,
        }


class LastKnownMammogramPresenter:
    def __init__(self, last_known_screening):
        self._last_known_screening = last_known_screening

    @cached_property
    def last_known_mammogram(self):
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


class ClinicSlotPresenter:
    def __init__(self, clinic_slot):
        self._clinic_slot = clinic_slot
        self._clinic = clinic_slot.clinic

        self.clinic_id = self._clinic.id

    @cached_property
    def clinic_type(self):
        return self._clinic.get_type_display().capitalize()

    @cached_property
    def slot_time_and_clinic_date(self):
        clinic_slot = self._clinic_slot
        clinic = self._clinic

        return f"{format_time(clinic_slot.starts_at)} ({clinic_slot.duration_in_minutes} minutes) - {format_date(clinic.starts_at)} ({format_relative_date(clinic.starts_at)})"

    @cached_property
    def starts_at(self):
        return format_time(self._clinic_slot.starts_at)
