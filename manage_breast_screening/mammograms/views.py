import logging
from functools import cached_property

from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.decorators.http import require_http_methods
from django.views.generic import FormView, TemplateView

from ..participants.models import (
    Appointment,
    AppointmentStatus,
    Participant,
    ParticipantReportedMammogram,
)
from .forms import (
    AppointmentCannotGoAheadForm,
    AskForMedicalInformationForm,
    RecordMedicalInformationForm,
    ScreeningAppointmentForm,
)
from .presenters import (
    AppointmentPresenter,
    LastKnownMammogramPresenter,
    present_secondary_nav,
)

APPOINTMENT_CANNOT_PROCEED = "Appointment cannot proceed"

logger = logging.getLogger(__name__)


class AppointmentMixin:
    """
    A view mixin that exposes the appointment.
    """

    @property
    def appointment_pk(self):
        return self.kwargs["pk"]

    @cached_property
    def appointment(self):
        return get_object_or_404(
            Appointment.objects.select_related(
                "clinic_slot__clinic",
                "screening_episode__participant",
                "screening_episode__participant__address",
            ),
            pk=self.appointment_pk,
        )


class InProgressAppointmentMixin(AppointmentMixin):
    """
    A view that is only shown with in progress appointments.
    If the appointment is not in progress, redirect to the appointment show page.
    """

    def dispatch(self, request, *args, **kwargs):
        appointment = self.appointment  # type: ignore
        if not appointment.current_status.in_progress:
            return redirect(
                "mammograms:show_appointment",
                pk=appointment.pk,
            )
        return super().dispatch(request, *args, **kwargs)  # type: ignore


class ShowAppointment(AppointmentMixin, View):
    """
    Show a completed appointment. Redirects to the start screening form
    if the apppointment is in progress.
    """

    template_name = "mammograms/show.jinja"

    def get(self, request, *args, **kwargs):
        appointment = self.appointment
        if appointment.current_status.in_progress:
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
            "title": appointment_presenter.participant.full_name,
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
                "title": appointment_presenter.participant.full_name,
                "caption": appointment_presenter.caption,
                "page_title": appointment_presenter.caption,
                "presented_appointment": appointment_presenter,
                "presented_participant": appointment_presenter.participant,
                "presented_mammograms": last_known_mammogram_presenter,
                "decision_legend": "Can the appointment go ahead?",
                "decision_hint": "Before you proceed, check the participant’s identity and confirm that their last mammogram was more than 6 months ago.",
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
                "title": "Medical information",
                "page_title": "Medical information",
                "decision_legend": "Has the participant shared any relevant medical information?",
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
                "title": "Record medical information",
                "page_title": "Record medical information",
                "participant": participant,
                "caption": participant.full_name,
                "decision_legend": "Can imaging go ahead?",
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
                "title": "Appointment cannot go ahead",
                "caption": participant.full_name,
                "page_title": "Appointment cannot go ahead",
                "decision_legend": "Does the appointment need to be rescheduled?",
            }
        )
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.appointment
        return kwargs

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class AwaitingImages(InProgressAppointmentMixin, TemplateView):
    template_name = "mammograms/awaiting_images.jinja"

    def get_context_data(self, **kwargs):
        return {"title": "Awaiting images", "page_title": "Awaiting images"}


@require_http_methods(["POST"])
def check_in(_request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    appointment.statuses.create(state=AppointmentStatus.CHECKED_IN)

    return redirect("mammograms:start_screening", pk=pk)
