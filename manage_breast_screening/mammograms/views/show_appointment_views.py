from django.shortcuts import render
from django.views import View

from manage_breast_screening.mammograms.presenters.appointment_presenters import (
    ImagesPresenterFactory,
)
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
        appointment_presenter = AppointmentPresenter(
            appointment, tab_description="Appointment details"
        )

        context = {
            "heading": appointment_presenter.participant.full_name,
            "caption": appointment_presenter.caption,
            "page_title": appointment_presenter.page_title,
            "presented_appointment": appointment_presenter,
            "presented_participant": appointment_presenter.participant,
            "appointment_note": appointment_presenter.note,
            "secondary_nav_items": present_secondary_nav(
                appointment,
                current_tab="appointment",
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
        appointment_presenter = AppointmentPresenter(appointment)

        context = {
            "heading": appointment_presenter.participant.full_name,
            "caption": appointment_presenter.caption,
            "page_title": appointment_presenter.caption,
            "presented_appointment": appointment_presenter,
            "presented_participant": appointment_presenter.participant,
            "secondary_nav_items": present_secondary_nav(
                appointment,
                current_tab="participant",
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
        reported_mammograms = (
            ParticipantReportedMammogram.objects.filter(appointment_id=appointment.pk)
            .select_related(
                "created_by",
                "appointment__clinic_slot__clinic__setting__provider",
            )
            .order_by("-created_at")
        )

        last_known_mammogram_presenter = LastKnownMammogramPresenter(
            self.request.user,
            reported_mammograms=reported_mammograms,
            last_confirmed_mammogram=appointment.participant.last_confirmed_mammogram,
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
                appointment,
                current_tab="medical_information",
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

        context = {
            "heading": appointment_presenter.participant.full_name,
            "caption": appointment_presenter.caption,
            "page_title": appointment_presenter.caption,
            "presented_appointment": appointment_presenter,
            "presented_images": ImagesPresenterFactory.presenter_for(appointment),
            "secondary_nav_items": present_secondary_nav(
                appointment,
                current_tab="images",
            ),
        }

        return render(
            request,
            template_name="mammograms/show/images.jinja",
            context=context,
        )
