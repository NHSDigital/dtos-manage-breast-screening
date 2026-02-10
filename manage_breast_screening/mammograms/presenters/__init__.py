from django.urls import reverse

from .appointment_presenters import (
    AppointmentPresenter,
    ClinicSlotPresenter,
    ParticipantPresenter,
    SpecialAppointmentPresenter,
)
from .last_known_mammogram_presenter import LastKnownMammogramPresenter


def present_secondary_nav(pk, current_tab=None, appointment_complete=False):
    """
    Build a secondary nav for reviewing the information of screened/partially screened appointments.
    """
    tabs = [
        {
            "id": "appointment",
            "text": "Appointment",
            "href": reverse("mammograms:show_appointment", kwargs={"pk": pk}),
            "current": current_tab == "appointment",
        },
        {
            "id": "participant",
            "text": "Participant",
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
            "id": "note",
            "text": "Note",
            "href": reverse("mammograms:appointment_note", kwargs={"pk": pk}),
            "current": current_tab == "note",
        },
    ]

    if appointment_complete:
        tabs.insert(
            -1,
            {
                "id": "images",
                "text": "Images",
                "href": reverse(
                    "mammograms:appointment_image_details", kwargs={"pk": pk}
                ),
                "current": current_tab == "images",
            },
        )

    return tabs


__all__ = [
    "AppointmentPresenter",
    "ParticipantPresenter",
    "ClinicSlotPresenter",
    "LastKnownMammogramPresenter",
    "SpecialAppointmentPresenter",
]
