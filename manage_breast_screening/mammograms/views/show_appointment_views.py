from django.shortcuts import render
from django.views import View

from manage_breast_screening.mammograms.presenters.appointment_presenters import (
    ImagesPresenterFactory,
)

from ..presenters import (
    AppointmentPresenter,
    LastKnownMammogramPresenter,
    present_secondary_nav,
)
from ..presenters.medical_information_presenter import MedicalInformationPresenter
from .mixins import AppointmentTabMixin


class ShowAppointmentView(AppointmentTabMixin, View):
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


class ShowParticipantDetailsView(AppointmentTabMixin, View):
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


class ShowMedicalInformationView(AppointmentTabMixin, View):
    def get(self, request, *args, **kwargs):
        appointment = self.appointment
        participant = appointment.participant
        last_confirmed_mammogram = participant.last_confirmed_mammogram
        reported_mammograms = self.appointment.recent_reported_mammograms(
            since_date=last_confirmed_mammogram.exact_date
            if last_confirmed_mammogram
            else None
        )

        presented_mammograms = LastKnownMammogramPresenter(
            self.request.user,
            reported_mammograms=reported_mammograms,
            last_confirmed_mammogram=last_confirmed_mammogram,
            appointment_pk=self.appointment.pk,
            current_url=self.request.path,
        )

        medical_information_presenter = MedicalInformationPresenter(appointment)
        appointment_presenter = medical_information_presenter.appointment
        context = {
            "heading": appointment_presenter.participant.full_name,
            "caption": appointment_presenter.caption,
            "page_title": appointment_presenter.caption,
            "presented_appointment": appointment_presenter,
            "presenter": medical_information_presenter,
            "presented_mammograms": presented_mammograms,
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


class ShowImageDetailsView(AppointmentTabMixin, View):
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
