from django.shortcuts import render
from django.views import View

from manage_breast_screening.participants.models import ParticipantReportedMammogram

from ..presenters import (
    AppointmentPresenter,
    LastKnownMammogramPresenter,
    present_secondary_nav,
)
from .mixins import AppointmentTabMixin

MAMMOGRAMS_RECORD_MEDICAL_INFORMATION_VIEWNAME = "mammograms:record_medical_information"


class ShowAppointment(AppointmentTabMixin, View):
    """
    Show a completed appointment. Redirects to the start screening form
    if the apppointment is in progress.
    """

    def get(self, request, *args, **kwargs):
        appointment = self.appointment
        last_known_mammograms = ParticipantReportedMammogram.objects.filter(
            appointment_id=appointment.pk
        ).order_by("-created_at")
        appointment_presenter = AppointmentPresenter(
            appointment, tab_description="Appointment details"
        )
        last_known_mammogram_presenter = LastKnownMammogramPresenter(
            last_known_mammograms,
            appointment_pk=appointment.pk,
            current_url=self.request.path,
        )

        context = {
            "heading": appointment_presenter.participant.full_name,
            "caption": appointment_presenter.caption,
            "page_title": appointment_presenter.page_title,
            "presented_appointment": appointment_presenter,
            "presented_participant": appointment_presenter.participant,
            "presented_mammograms": last_known_mammogram_presenter,
            "appointment_note": appointment_presenter.note,
            "secondary_nav_items": present_secondary_nav(
                appointment.pk, current_tab="appointment"
            ),
        }

        return render(
            request,
            template_name="mammograms/show/appointment_details.jinja",
            context=context,
        )


class ParticipantDetails(AppointmentTabMixin, View):
    def get(self, request, *args, **kwargs):
        appointment = self.appointment
        last_known_mammograms = ParticipantReportedMammogram.objects.filter(
            appointment_id=appointment.pk
        ).order_by("-created_at")
        appointment_presenter = AppointmentPresenter(appointment)
        last_known_mammogram_presenter = LastKnownMammogramPresenter(
            last_known_mammograms,
            appointment_pk=appointment.pk,
            current_url=self.request.path,
        )

        context = {
            "heading": appointment_presenter.participant.full_name,
            "caption": appointment_presenter.caption,
            "page_title": appointment_presenter.caption,
            "presented_appointment": appointment_presenter,
            "presented_participant": appointment_presenter.participant,
            "presented_mammograms": last_known_mammogram_presenter,
            "secondary_nav_items": present_secondary_nav(
                appointment.pk, current_tab="participant"
            ),
        }

        return render(
            request,
            template_name="mammograms/show/participant_details.jinja",
            context=context,
        )
