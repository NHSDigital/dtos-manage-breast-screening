from django.urls import reverse

from .appointment_presenters import (
    AppointmentPresenter,
    ClinicSlotPresenter,
    SpecialAppointmentPresenter,
)
from .last_known_mammogram_presenter import LastKnownMammogramPresenter


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
        {"id": "note", "text": "Note", "href": "#"},
    ]


__all__ = [
    "AppointmentPresenter",
    "ClinicSlotPresenter",
    "LastKnownMammogramPresenter",
    "SpecialAppointmentPresenter",
]
