import logging

from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.decorators.http import require_http_methods
from django.views.generic import FormView, TemplateView

from manage_breast_screening.core.services.auditor import Auditor
from manage_breast_screening.mammograms.services.appointment_services import (
    AppointmentStatusUpdater,
)
from manage_breast_screening.participants.models import (
    Appointment,
    Participant,
    ParticipantReportedMammogram,
)

from ..forms import (
    AppointmentCannotGoAheadForm,
    AskForMedicalInformationForm,
    RecordMedicalInformationForm,
)
from ..presenters import (
    AppointmentPresenter,
    LastKnownMammogramPresenter,
    present_secondary_nav,
)
from ..presenters.medical_information_presenter import MedicalInformationPresenter
from .mixins import AppointmentMixin, InProgressAppointmentMixin

APPOINTMENT_CANNOT_PROCEED = "Appointment cannot proceed"

logger = logging.getLogger(__name__)


class ShowAppointment(AppointmentMixin, View):
    """
    Show a completed appointment. Redirects to the start screening form
    if the apppointment is in progress.
    """

    template_name = "mammograms/show.jinja"

    def get(self, request, *args, **kwargs):
        appointment = self.appointment
        participant_pk = appointment.screening_episode.participant.pk
        last_known_mammograms = ParticipantReportedMammogram.objects.filter(
            participant_id=participant_pk
        ).order_by("-created_at")
        appointment_presenter = AppointmentPresenter(appointment)
        last_known_mammogram_presenter = LastKnownMammogramPresenter(
            last_known_mammograms,
            participant_pk=participant_pk,
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
                appointment.pk, current_tab="appointment"
            ),
        }

        return render(
            request,
            template_name="mammograms/show/appointment_details.jinja",
            context=context,
        )


class ParticipantDetails(AppointmentMixin, View):
    """
    Show a completed appointment. Redirects to the start screening form
    if the apppointment is in progress.
    """

    template_name = "mammograms/show.jinja"

    def get(self, request, *args, **kwargs):
        appointment = self.appointment
        participant_pk = appointment.screening_episode.participant.pk
        last_known_mammograms = ParticipantReportedMammogram.objects.filter(
            participant_id=participant_pk
        ).order_by("-created_at")
        appointment_presenter = AppointmentPresenter(appointment)
        last_known_mammogram_presenter = LastKnownMammogramPresenter(
            last_known_mammograms,
            participant_pk=participant_pk,
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


class AskForMedicalInformation(InProgressAppointmentMixin, FormView):
    template_name = "mammograms/ask_for_medical_information.jinja"
    form_class = AskForMedicalInformationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs["pk"]
        provider = self.request.user.current_provider
        participant = provider.participants.get(screeningepisode__appointment__pk=pk)

        context.update(
            {
                "participant": participant,
                "caption": participant.full_name,
                "heading": "Medical information",
                "page_title": "Medical information",
                "cannot_continue_link": {
                    "href": reverse(
                        "mammograms:appointment_cannot_go_ahead",
                        kwargs={"pk": pk},
                    ),
                    "text": APPOINTMENT_CANNOT_PROCEED,
                },
            }
        )

        return context

    def form_valid(self, form):
        form.save()

        appointment = self.appointment

        if form.cleaned_data["decision"] == "yes":
            return redirect("mammograms:record_medical_information", pk=appointment.pk)
        else:
            return redirect("mammograms:awaiting_images", pk=appointment.pk)


class RecordMedicalInformation(InProgressAppointmentMixin, FormView):
    template_name = "mammograms/record_medical_information.jinja"
    form_class = RecordMedicalInformationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs["pk"]
        provider = self.request.user.current_provider
        try:
            participant = provider.participants.get(
                screeningepisode__appointment__pk=pk,
            )
        except Participant.DoesNotExist:
            raise Http404("Participant not found")
        context.update(
            {
                "heading": "Record medical information",
                "page_title": "Record medical information",
                "participant": participant,
                "caption": participant.full_name,
                "presenter": MedicalInformationPresenter(self.appointment),
            }
        )

        return context

    def form_valid(self, form):
        form.save()

        appointment = self.appointment

        if form.cleaned_data["decision"] == "continue":
            return redirect("mammograms:awaiting_images", pk=appointment.pk)
        else:
            return redirect("mammograms:appointment_cannot_go_ahead", pk=appointment.pk)


class AppointmentCannotGoAhead(InProgressAppointmentMixin, FormView):
    template_name = "mammograms/appointment_cannot_go_ahead.jinja"
    form_class = AppointmentCannotGoAheadForm
    success_url = reverse_lazy("clinics:index")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        provider = self.request.user.current_provider
        participant = provider.participants.get(
            screeningepisode__appointment__pk=self.appointment.pk
        )
        context.update(
            {
                "heading": "Appointment cannot go ahead",
                "caption": participant.full_name,
                "page_title": "Appointment cannot go ahead",
            }
        )
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.appointment
        return kwargs

    def form_valid(self, form):
        instance = form.save()
        Auditor.from_request(self.request).audit_update(instance)
        return super().form_valid(form)


class AwaitingImages(InProgressAppointmentMixin, TemplateView):
    template_name = "mammograms/awaiting_images.jinja"

    def get_context_data(self, **kwargs):
        return {"heading": "Awaiting images", "page_title": "Awaiting images"}


@require_http_methods(["POST"])
def check_in(request, pk):
    try:
        provider = request.user.current_provider
        appointment = provider.appointments.get(pk=pk)
    except Appointment.DoesNotExist:
        raise Http404("Appointment not found")

    AppointmentStatusUpdater(
        appointment=appointment, current_user=request.user
    ).check_in()

    return redirect("mammograms:show_appointment", pk=pk)


@require_http_methods(["POST"])
def start_appointment(request, pk):
    try:
        provider = request.user.current_provider
        appointment = provider.appointments.get(pk=pk)
    except Appointment.DoesNotExist:
        raise Http404("Appointment not found")

    AppointmentStatusUpdater(appointment=appointment, current_user=request.user).start()

    return redirect("mammograms:ask_for_medical_information", pk=pk)
