from django.shortcuts import render
from django.views import View

from manage_breast_screening.mammograms.presenters.appointment_presenters import (
    GatewayImagesPresenter,
    ImagesTakenPresenter,
)
from manage_breast_screening.mammograms.views import gateway_images_enabled
from manage_breast_screening.participants.models import ParticipantReportedMammogram

from ..presenters import (
    AppointmentPresenter,
    LastKnownMammogramPresenter,
    present_secondary_nav,
)
from ..presenters.medical_information_presenter import MedicalInformationPresenter
from .mixins import AppointmentTabMixin


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
                appointment.pk,
                current_tab="appointment",
                appointment_complete=not appointment.active,
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
                appointment.pk,
                current_tab="participant",
                appointment_complete=not appointment.active,
            ),
        }

        return render(
            request,
            template_name="mammograms/show/participant_details.jinja",
            context=context,
        )


class MedicalInformation(AppointmentTabMixin, View):
    def get(self, request, *args, **kwargs):
        appointment = self.appointment
        appointment_presenter = AppointmentPresenter(appointment)
        last_known_mammograms = ParticipantReportedMammogram.objects.filter(
            appointment_id=appointment.pk
        ).order_by("-created_at")
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
            "presenter": MedicalInformationPresenter(appointment),
            "presented_mammograms": last_known_mammogram_presenter,
            "secondary_nav_items": present_secondary_nav(
                appointment.pk,
                current_tab="medical_information",
                appointment_complete=not appointment.active,
            ),
        }

        return render(
            request,
            template_name="mammograms/show/medical_information.jinja",
            context=context,
        )


class ImageDetails(AppointmentTabMixin, View):
    def get(self, request, *args, **kwargs):
        appointment = self.appointment
        appointment_presenter = AppointmentPresenter(appointment)
        images_presenter = (
            GatewayImagesPresenter
            if gateway_images_enabled(appointment)
            else ImagesTakenPresenter
        )

        context = {
            "heading": appointment_presenter.participant.full_name,
            "caption": appointment_presenter.caption,
            "page_title": appointment_presenter.caption,
            "presented_appointment": appointment_presenter,
            "presented_images": images_presenter(appointment),
            "secondary_nav_items": present_secondary_nav(
                appointment.pk,
                current_tab="images",
                appointment_complete=not appointment.active,
            ),
        }

        return render(
            request,
            template_name="mammograms/show/images.jinja",
            context=context,
        )
