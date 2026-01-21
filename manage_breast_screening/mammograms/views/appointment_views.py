import logging

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.db import DatabaseError, IntegrityError, transaction
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.decorators.http import require_http_methods
from django.views.generic import FormView, TemplateView

from manage_breast_screening.auth.models import Permission
from manage_breast_screening.core.services.auditor import Auditor
from manage_breast_screening.mammograms.services.appointment_services import (
    AppointmentStatusUpdater,
)
from manage_breast_screening.participants.models import (
    Appointment,
    MedicalInformationSection,
    ParticipantReportedMammogram,
)
from manage_breast_screening.participants.models.appointment import (
    AppointmentWorkflowStepCompletion,
)
from manage_breast_screening.participants.presenters import ParticipantPresenter

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
from .mixins import AppointmentTabMixin, InProgressAppointmentMixin

APPOINTMENT_CANNOT_PROCEED = "Appointment cannot proceed"

logger = logging.getLogger(__name__)


class ShowAppointment(AppointmentTabMixin, View):
    """
    Show a completed appointment. Redirects to the start screening form
    if the apppointment is in progress.
    """

    template_name = "mammograms/show.jinja"

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
    template_name = "mammograms/show.jinja"

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


class ConfirmIdentity(InProgressAppointmentMixin, TemplateView):
    template_name = "mammograms/confirm_identity.jinja"

    def get_context_data(self, pk, **kwargs):
        context = super().get_context_data()

        participant = self.appointment.participant

        context.update(
            {
                "heading": "Confirm identity",
                "page_title": "Confirm identity",
                "presented_participant": ParticipantPresenter(participant),
                "appointment_cannot_proceed_href": reverse(
                    "mammograms:appointment_cannot_go_ahead", kwargs={"pk": pk}
                ),
            },
        )

        return context

    def post(self, request, pk):
        self.appointment.completed_workflow_steps.create(
            step_name=AppointmentWorkflowStepCompletion.StepNames.CONFIRM_IDENTITY,
            created_by=request.user,
        )

        return redirect("mammograms:ask_for_medical_information", pk=pk)


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
        participant = self.participant
        last_known_mammograms = ParticipantReportedMammogram.objects.filter(
            appointment_id=self.appointment.pk
        ).order_by("-created_at")

        presented_mammograms = LastKnownMammogramPresenter(
            last_known_mammograms,
            appointment_pk=self.appointment.pk,
            current_url=self.request.path,
        )

        context.update(
            {
                "heading": "Record medical information",
                "page_title": "Record medical information",
                "participant": participant,
                "caption": participant.full_name,
                "presenter": MedicalInformationPresenter(self.appointment),
                "presented_mammograms": presented_mammograms,
                "sections": MedicalInformationSection,
            }
        )

        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["appointment"] = self.appointment
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        try:
            with transaction.atomic():
                form.save()
            return redirect("mammograms:awaiting_images", pk=self.appointment.pk)
        except (IntegrityError, DatabaseError):
            messages.add_message(
                self.request,
                messages.WARNING,
                "Unable to complete all sections. Please try again.",
            )
            return redirect(
                "mammograms:record_medical_information", pk=self.appointment.pk
            )


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
@permission_required(Permission.START_MAMMOGRAM_APPOINTMENT)
def start_appointment(request, pk):
    try:
        provider = request.user.current_provider
        appointment = provider.appointments.get(pk=pk)
    except Appointment.DoesNotExist:
        raise Http404("Appointment not found")

    AppointmentStatusUpdater(appointment=appointment, current_user=request.user).start()

    return redirect("mammograms:confirm_identity", pk=pk)


class MarkSectionReviewed(InProgressAppointmentMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        section = kwargs.get("section")

        valid_sections = [choice[0] for choice in MedicalInformationSection.choices]
        if section not in valid_sections:
            raise Http404("Invalid section")

        existing_review = self.appointment.medical_information_reviews.filter(
            section=section
        ).first()

        if existing_review:
            messages.add_message(
                request,
                messages.WARNING,
                f"This section has already been reviewed by {existing_review.reviewed_by.get_full_name()}",
            )
            return redirect(
                "mammograms:record_medical_information", pk=self.appointment.pk
            )

        self.appointment.medical_information_reviews.create(
            section=section,
            reviewed_by=request.user,
        )

        return redirect("mammograms:record_medical_information", pk=self.appointment.pk)
