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
            "href": reverse("mammograms:show_appointment", kwargs={"pk": pk}),
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
        self.screening_protocol = appointment.screening_episode.get_protocol_display()

    @cached_property
    def participant_url(self):
        return self.participant.url

    @cached_property
    def start_time(self):
        return self.clinic_slot.starts_at

    @cached_property
    def is_special_appointment(self):
        return bool(self.participant.extra_needs)

    @cached_property
    def special_appointment_tag_properties(self):
        return {
            "classes": "nhsuk-tag--yellow nhsuk-u-margin-top-2",
            "text": "Special appointment",
        }

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
    def __init__(self, last_known_mammograms, participant_pk, current_url):
        self._last_known_mammograms = last_known_mammograms
        self.participant_pk = participant_pk
        self.current_url = current_url

    @cached_property
    def last_known_mammograms(self):
        result = []
        for mammogram in self._last_known_mammograms:
            result.append(self._present_mammogram(mammogram))

        return result

    def _present_mammogram(self, mammogram):
        location = (
            mammogram.provider.name
            if mammogram.provider
            else mammogram.location_details
        )
        if mammogram.provider:
            location = mammogram.provider.name
        elif (
            mammogram.location_details
            and mammogram.location_type == mammogram.LocationType.ELSEWHERE_UK
        ):
            location = f"In the UK: {mammogram.location_details}"
        elif (
            mammogram.location_details
            and mammogram.location_type == mammogram.LocationType.OUTSIDE_UK
        ):
            location = f"Outside the UK: {mammogram.location_details}"
        elif mammogram.location_type == mammogram.LocationType.PREFER_NOT_TO_SAY:
            location = "Location: prefer not to say"
        else:
            location = "Location unknown"

        if mammogram.exact_date:
            absolute = format_date(mammogram.exact_date)
            relative = format_relative_date(mammogram.exact_date)
            date = {"absolute": absolute, "relative": relative, "is_exact": True}
        elif mammogram.approx_date:
            date = {"value": f"Approximate date: {mammogram.approx_date}"}
        else:
            date = {"value": "Date unknown"}

        return {
            "date_added": format_relative_date(mammogram.created_at),
            "location": location,
            "date": date,
            "different_name": mammogram.different_name,
            "additional_information": mammogram.additional_information,
        }

    @cached_property
    def add_link(self):
        href = (
            reverse(
                "participants:add_previous_mammogram",
                kwargs={"pk": self.participant_pk},
            )
            + f"?return_url={self.current_url}"
        )
        return {
            "href": href,
            "text": "Add another" if self.last_known_mammograms else "Add",
            "visually_hidden_text": "mammogram",
        }


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
