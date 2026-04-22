from django.urls import reverse

from .appointment_presenters import (
    AppointmentPresenter,
    ClinicSlotPresenter,
    ParticipantPresenter,
    SpecialAppointmentPresenter,
)
from .last_known_mammogram_presenter import LastKnownMammogramPresenter


def present_secondary_nav(appointment, current_tab=None):
    """
    Build a secondary nav for reviewing the information of screened/partially screened appointments.
    """
    pk = appointment.pk

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
            "href": reverse("mammograms:show_participant_details", kwargs={"pk": pk}),
            "current": current_tab == "participant",
        },
        {
            "id": "medical_information",
            "text": "Medical information",
            "href": reverse("mammograms:show_medical_information", kwargs={"pk": pk}),
            "current": current_tab == "medical_information",
        },
        {
            "id": "note",
            "text": "Note",
            "href": reverse("mammograms:upsert_appointment_note", kwargs={"pk": pk}),
            "current": current_tab == "note",
        },
    ]

    if appointment.has_study():
        tabs.insert(
            -1,
            {
                "id": "images",
                "text": "Images",
                "href": reverse("mammograms:show_image_details", kwargs={"pk": pk}),
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
