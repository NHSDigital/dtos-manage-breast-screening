import logging

from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.generic import FormView

from ..participants.models import Appointment, AppointmentStatus, Participant
from .forms import (
    AppointmentCannotGoAheadForm,
    AskForMedicalInformationForm,
    RecordMedicalInformationForm,
    ScreeningAppointmentForm,
)
from .presenters import AppointmentPresenter, present_secondary_nav

APPOINTMENT_CANNOT_PROCEED = "Appointment cannot proceed"

logger = logging.getLogger(__name__)


class BaseAppointmentForm(FormView):
    @property
    def appointment_pk(self):
        return self.kwargs["pk"]

    def get_appointment(self):
        return get_object_or_404(
            Appointment.objects.prefetch_related(
                "clinic_slot",
                "screening_episode__participant",
                "screening_episode__participant__address",
            ),
            pk=self.appointment_pk,
        )


class StartScreening(BaseAppointmentForm):
    template_name = "mammograms/start_screening.jinja"
    form_class = ScreeningAppointmentForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        appointment = self.get_appointment()
        last_known_screening = appointment.screening_episode.previous()
        presenter = AppointmentPresenter(appointment, last_known_screening)

        context.update(
            {
                "title": presenter.participant.full_name,
                "caption": presenter.clinic_slot.clinic_type + " appointment",
                "appointment": presenter,
                "decision_legend": "Can the appointment go ahead?",
                "decision_hint": "Before you proceed, check the participant’s identity and confirm that their last mammogram was more than 6 months ago.",
            }
        )

        if AppointmentStatus in [
            AppointmentStatus.SCREENED,
            AppointmentStatus.PARTIALLY_SCREENED,
        ]:
            context["secondary_nav_items"] = present_secondary_nav(appointment.pk)

        return context

    def form_valid(self, form):
        form.save()

        if form.cleaned_data["decision"] == "continue":
            return redirect(
                "mammograms:ask_for_medical_information",
                pk=self.get_appointment().pk,
            )
        else:
            return redirect(
                "mammograms:appointment_cannot_go_ahead",
                pk=self.get_appointment().pk,
            )


class AskForMedicalInformation(BaseAppointmentForm):
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

        appointment = self.get_appointment()

        if form.cleaned_data["decision"] == "yes":
            return redirect("mammograms:record_medical_information", pk=appointment.pk)
        else:
            return redirect("mammograms:awaiting_images", pk=appointment.pk)


class RecordMedicalInformation(BaseAppointmentForm):
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
                "participant": participant,
                "caption": participant.full_name,
                "decision_legend": "Can imaging go ahead?",
            }
        )
        return context

    def form_valid(self, form):
        form.save()

        appointment = self.get_appointment()

        if form.cleaned_data["decision"] == "continue":
            return redirect("mammograms:awaiting_images", pk=appointment.pk)
        else:
            return redirect("mammograms:appointment_cannot_go_ahead", pk=appointment.pk)


def appointment_cannot_go_ahead(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    participant = appointment.screening_episode.participant

    if request.method == "POST":
        form = AppointmentCannotGoAheadForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            return redirect("clinics:index")
    else:
        form = AppointmentCannotGoAheadForm(instance=appointment)

    return render(
        request,
        "mammograms/appointment_cannot_go_ahead.jinja",
        {
            "title": "Appointment cannot go ahead",
            "caption": participant.full_name,
            "form": form,
            "decision_legend": "Does the appointment need to be rescheduled?",
        },
    )


def awaiting_images(request, pk):
    return render(
        request,
        "mammograms/awaiting_images.jinja",
        {"title": "Awaiting images"},
    )


@require_http_methods(["POST"])
def check_in(_request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    appointment.statuses.create(state=AppointmentStatus.CHECKED_IN)

    return redirect("mammograms:start_screening", pk=pk)
