from django.urls import reverse

from .appointment_presenters import (
    AppointmentPresenter,
    ClinicSlotPresenter,
    ParticipantPresenter,
    SpecialAppointmentPresenter,
)
from .last_known_mammogram_presenter import LastKnownMammogramPresenter


def present_secondary_nav(pk, current_tab=None):
    """
    Build a secondary nav for reviewing the information of screened/partially screened appointments.
    """
    return [
        {
            "id": "appointment",
            "text": "Appointment details",
            "href": reverse("mammograms:show_appointment", kwargs={"pk": pk}),
            "current": current_tab == "appointment",
        },
        {
            "id": "participant",
            "text": "Participant details",
            "href": reverse("mammograms:participant_details", kwargs={"pk": pk}),
            "current": current_tab == "participant",
        },
        {
            "id": "medical_information",
            "text": "Medical information",
            "href": "#",
            "current": current_tab == "medical_information",
        },
        {
            "id": "images",
            "text": "Images",
            "href": "#",
            "current": current_tab == "images",
        },
        {
            "id": "note",
            "text": "Note",
            "href": reverse("mammograms:appointment_note", kwargs={"pk": pk}),
            "current": current_tab == "note",
        },
    ]


__all__ = [
    "AppointmentPresenter",
    "ParticipantPresenter",
    "ClinicSlotPresenter",
    "LastKnownMammogramPresenter",
    "SpecialAppointmentPresenter",
]
