import logging

from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.decorators.http import require_http_methods
from django.views.generic import FormView, TemplateView

from manage_breast_screening.auth.models import Permission
from manage_breast_screening.core.services.auditor import Auditor
from manage_breast_screening.participants.models import (
    Appointment,
    AppointmentStatus,
    Participant,
    ParticipantReportedMammogram,
)

from ..forms import (
    AppointmentCannotGoAheadForm,
    AskForMedicalInformationForm,
    RecordMedicalInformationForm,
    ScreeningAppointmentForm,
)
from ..presenters import (
    AppointmentPresenter,
    LastKnownMammogramPresenter,
    MedicalInformationPresenter,
    present_secondary_nav,
)
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
        if (
            request.user.has_perm(Permission.PERFORM_MAMMOGRAM_APPOINTMENT)
            and appointment.current_status.in_progress
        ):
            return redirect("mammograms:start_screening", pk=self.appointment.pk)

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
            "secondary_nav_items": present_secondary_nav(appointment.pk),
        }

        return render(
            request,
            template_name="mammograms/show/appointment_details.jinja",
            context=context,
        )


class StartScreening(InProgressAppointmentMixin, FormView):
    template_name = "mammograms/start_screening.jinja"
    form_class = ScreeningAppointmentForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

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

        context.update(
            {
                "heading": appointment_presenter.participant.full_name,
                "caption": appointment_presenter.caption,
                "page_title": appointment_presenter.caption,
                "presented_appointment": appointment_presenter,
                "presented_participant": appointment_presenter.participant,
                "presented_mammograms": last_known_mammogram_presenter,
            }
        )

        return context

    def form_valid(self, form):
        form.save()

        if form.cleaned_data["decision"] == "continue":
            return redirect(
                "mammograms:ask_for_medical_information",
                pk=self.appointment.pk,
            )
        else:
            return redirect(
                "mammograms:appointment_cannot_go_ahead",
                pk=self.appointment.pk,
            )


class AskForMedicalInformation(InProgressAppointmentMixin, FormView):
    template_name = "mammograms/ask_for_medical_information.jinja"
    form_class = AskForMedicalInformationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs["pk"]
        participant = Participant.objects.get(screeningepisode__appointment__pk=pk)

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
        participant = get_object_or_404(
            Participant, screeningepisode__appointment__pk=pk
        )
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

        participant = self.appointment.screening_episode.participant
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
    appointment = get_object_or_404(Appointment, pk=pk)
    status = appointment.statuses.create(state=AppointmentStatus.CHECKED_IN)

    Auditor.from_request(request).audit_create(status)

    return redirect("mammograms:start_screening", pk=pk)
