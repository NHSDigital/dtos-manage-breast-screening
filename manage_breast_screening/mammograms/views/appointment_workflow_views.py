import logging
import time

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ValidationError
from django.db import DatabaseError, IntegrityError, transaction
from django.forms import Form
from django.http import Http404, StreamingHttpResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.decorators.http import require_http_methods
from django.views.generic import FormView, TemplateView

from manage_breast_screening.auth.models import Permission
from manage_breast_screening.core.services.auditor import Auditor
from manage_breast_screening.gateway.worklist_item_service import (
    GatewayActionAlreadyExistsError,
    WorklistItemService,
    get_images_for_appointment,
)
from manage_breast_screening.mammograms.forms.images.record_images_taken_form import (
    RecordImagesTakenForm,
)
from manage_breast_screening.mammograms.services.appointment_services import (
    AppointmentStatusUpdater,
    AppointmentWorkflowService,
)
from manage_breast_screening.manual_images.services import StudyService
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
    RecordMedicalInformationForm,
)
from ..presenters import LastKnownMammogramPresenter
from ..presenters.medical_information_presenter import MedicalInformationPresenter
from .mixins import InProgressAppointmentMixin

MAMMOGRAMS_RECORD_MEDICAL_INFORMATION_VIEWNAME = "mammograms:record_medical_information"

logger = logging.getLogger(__name__)


class ConfirmIdentity(InProgressAppointmentMixin, TemplateView):
    template_name = "mammograms/confirm_identity.jinja"
    CONFIRM_IDENTITY_LABEL = "Confirm identity"

    def get_context_data(self, pk, **kwargs):
        context = super().get_context_data()

        participant = self.appointment.participant

        context.update(
            {
                "heading": self.CONFIRM_IDENTITY_LABEL,
                "page_title": self.CONFIRM_IDENTITY_LABEL,
                "presented_participant": ParticipantPresenter(participant),
                "confirm_button_text": (
                    "Next section"
                    if AppointmentWorkflowService(
                        appointment=self.appointment, current_user=self.request.user
                    ).is_identity_confirmed_by_user()
                    else self.CONFIRM_IDENTITY_LABEL
                ),
                "appointment_cannot_proceed_href": reverse(
                    "mammograms:appointment_cannot_go_ahead", kwargs={"pk": pk}
                ),
            },
        )

        return context

    def post(self, request, pk):
        if not AppointmentWorkflowService(
            appointment=self.appointment, current_user=self.request.user
        ).is_identity_confirmed_by_user():
            self.appointment.completed_workflow_steps.create(
                step_name=AppointmentWorkflowStepCompletion.StepNames.CONFIRM_IDENTITY,
                created_by=request.user,
            )

        return redirect(MAMMOGRAMS_RECORD_MEDICAL_INFORMATION_VIEWNAME, pk=pk)


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
                "appointment_cannot_proceed_href": reverse(
                    "mammograms:appointment_cannot_go_ahead",
                    kwargs={
                        "pk": self.appointment.pk,
                    },
                ),
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
                WorklistItemService.create(self.appointment)
        except (IntegrityError, DatabaseError):
            messages.add_message(
                self.request,
                messages.WARNING,
                "Unable to complete all sections. Please try again.",
            )
            return redirect(
                MAMMOGRAMS_RECORD_MEDICAL_INFORMATION_VIEWNAME,
                pk=self.appointment.pk,
            )
        except GatewayActionAlreadyExistsError as e:
            logger.warning(str(e))

        return redirect("mammograms:take_images", pk=self.appointment.pk)


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
        instance = form.save(current_user=self.request.user)
        Auditor.from_request(self.request).audit_update(instance)

        return super().form_valid(form)


class TakeImages(InProgressAppointmentMixin, FormView):
    template_name = "mammograms/take_images.jinja"
    form_class = RecordImagesTakenForm

    def get(self, request, *args, **kwargs):
        if self.appointment.series().exists():
            return redirect("mammograms:update_image_details", pk=self.appointment_pk)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        images = get_images_for_appointment(self.appointment)
        context.update(
            {
                "heading": "Record images taken",
                "page_title": "Record images taken",
                "images": images,
                "appointment_pk": self.appointment.pk,
            }
        )
        return context

    @transaction.atomic
    def form_valid(self, form):
        form.save(
            StudyService(appointment=self.appointment, current_user=self.request.user)
        )

        match form.cleaned_data["standard_images"]:
            case form.StandardImagesChoices.YES_TWO_CC_AND_TWO_MLO:
                self.mark_workflow_step_complete()

                return redirect("mammograms:check_information", pk=self.appointment_pk)
            case form.StandardImagesChoices.NO_ADD_ADDITIONAL:
                return redirect(
                    "mammograms:add_image_details",
                    pk=self.appointment_pk,
                )
            case _:
                return redirect(
                    "mammograms:appointment_cannot_go_ahead",
                    pk=self.appointment_pk,
                )

    def mark_workflow_step_complete(self):
        self.appointment.completed_workflow_steps.get_or_create(
            step_name=AppointmentWorkflowStepCompletion.StepNames.TAKE_IMAGES,
            defaults={"created_by": self.request.user},
        )


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
@permission_required(Permission.DO_MAMMOGRAM_APPOINTMENT)
def start_appointment(request, pk):
    try:
        provider = request.user.current_provider
        appointment = provider.appointments.get(pk=pk)
    except Appointment.DoesNotExist:
        raise Http404("Appointment not found")

    AppointmentStatusUpdater(appointment=appointment, current_user=request.user).start()

    return redirect("mammograms:confirm_identity", pk=pk)


@require_http_methods(["POST"])
@permission_required(Permission.DO_MAMMOGRAM_APPOINTMENT)
def resume_appointment(request, pk):
    try:
        provider = request.user.current_provider
        appointment = provider.appointments.get(pk=pk)
    except Appointment.DoesNotExist:
        raise Http404("Appointment not found")

    if not appointment.current_status.is_in_progress_with(request.user):
        AppointmentStatusUpdater(
            appointment=appointment, current_user=request.user
        ).resume()

    next_step = "mammograms:confirm_identity"

    workflow_service = AppointmentWorkflowService(
        appointment=appointment, current_user=request.user
    )
    if workflow_service.is_identity_confirmed_by_user():
        completed_steps = workflow_service.get_completed_steps()
        if AppointmentWorkflowStepCompletion.StepNames.TAKE_IMAGES in completed_steps:
            next_step = "mammograms:check_information"
        elif (
            AppointmentWorkflowStepCompletion.StepNames.REVIEW_MEDICAL_INFORMATION
            in completed_steps
        ):
            next_step = "mammograms:take_images"
        else:
            next_step = "mammograms:record_medical_information"

    return redirect(next_step, pk=pk)


class PauseAppointment(InProgressAppointmentMixin, FormView):
    template_name = "mammograms/pause_appointment.jinja"
    form_class = Form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        provider = self.request.user.current_provider
        participant = provider.participants.get(
            screeningepisode__appointment__pk=self.appointment.pk
        )
        context.update(
            {
                "heading": "Pause this appointment",
                "caption": participant.full_name,
                "page_title": "Pause this appointment",
            }
        )
        return context

    def form_valid(self, form):
        try:
            provider = self.request.user.current_provider
            appointment = provider.appointments.get(pk=self.appointment.pk)
        except Appointment.DoesNotExist:
            raise Http404("Appointment not found")

        if not appointment.current_status.is_in_progress_with(self.request.user):
            raise ValidationError("Can't pause when not in progress with the user")

        AppointmentStatusUpdater(
            appointment=appointment, current_user=self.request.user
        ).pause()

        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "clinics:show", kwargs={"pk": self.appointment.clinic_slot.clinic.pk}
        )


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
        else:
            self.appointment.medical_information_reviews.create(
                section=section,
                reviewed_by=request.user,
            )

        return redirect(
            MAMMOGRAMS_RECORD_MEDICAL_INFORMATION_VIEWNAME, pk=self.appointment.pk
        )


def format_sse_event(event: str, data: str) -> str:
    """Format data as a Server-Sent Event."""
    lines = "\n".join(f"data: {line}" for line in data.splitlines())
    return f"event: {event}\n{lines}\n\n"


@login_required
@require_http_methods(["GET"])
def appointment_images_stream(request, pk):
    """SSE endpoint for streaming appointment images as they arrive."""
    try:
        provider = request.user.current_provider
        appointment = provider.appointments.get(pk=pk)
    except Appointment.DoesNotExist:
        raise Http404("Appointment not found")

    def event_stream():
        last_image_ids = set()

        while True:
            images = get_images_for_appointment(appointment)
            current_image_ids = set(str(img.id) for img in images)

            if current_image_ids != last_image_ids:
                html = render_to_string(
                    "mammograms/_image_grid.jinja",
                    {"images": images},
                    request=request,
                )
                yield format_sse_event("images", html)
                last_image_ids = current_image_ids

            time.sleep(1)

    response = StreamingHttpResponse(
        event_stream(),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
