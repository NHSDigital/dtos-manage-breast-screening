import logging
import time
from functools import cached_property
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ValidationError
from django.db import DatabaseError, IntegrityError, transaction
from django.forms import Form
from django.http import Http404, HttpResponse, StreamingHttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import escape, mark_safe
from django.views import View
from django.views.decorators.http import require_http_methods
from django.views.generic import FormView, TemplateView
from rules.contrib.views import PermissionRequiredMixin

from manage_breast_screening.auth.models import Permission
from manage_breast_screening.core.models import get_object_or_none
from manage_breast_screening.core.services.auditor import Auditor
from manage_breast_screening.core.utils.date_formatting import format_relative_date
from manage_breast_screening.core.utils.relative_redirects import (
    extract_relative_redirect_url,
)
from manage_breast_screening.core.views.generic import UpdateWithAuditView
from manage_breast_screening.dicom.models import Study as DicomStudy
from manage_breast_screening.dicom.study_service import (
    StudyService as DicomStudyService,
)
from manage_breast_screening.gateway.worklist_item_service import (
    GatewayActionAlreadyExistsError,
    WorklistItemService,
    get_images_for_appointment,
)
from manage_breast_screening.mammograms.forms.images.gateway_image_details_form import (
    GatewayImageDetailsForm,
)
from manage_breast_screening.mammograms.forms.images.record_images_taken_form import (
    RecordImagesTakenForm,
)
from manage_breast_screening.mammograms.presenters.appointment_presenters import (
    AppointmentPresenter,
    ImagesPresenterFactory,
    WorkflowPresenter,
)
from manage_breast_screening.mammograms.presenters.medical_history.check_medical_information_presenter import (
    CheckMedicalInformationPresenter,
)
from manage_breast_screening.mammograms.services.appointment_services import (
    AppointmentStatusUpdater,
    AppointmentWorkflowService,
    RecallService,
    StepNames,
)
from manage_breast_screening.mammograms.views import gateway_images_enabled
from manage_breast_screening.manual_images.models import Study
from manage_breast_screening.manual_images.services import StudyService
from manage_breast_screening.participants.models import (
    Appointment,
    MedicalInformationSection,
    ParticipantReportedMammogram,
)
from manage_breast_screening.participants.models.appointment import (
    AppointmentMachine,
    AppointmentStatusNames,
    AppointmentWorkflowStepCompletion,
)
from manage_breast_screening.participants.presenters import ParticipantPresenter

from ..forms import AppointmentCannotGoAheadForm, RecordMedicalInformationForm
from ..forms.appointment_proceed_anyway_form import AppointmentProceedAnywayForm
from ..forms.breast_feature_form import AddBreastFeatureForm, UpdateBreastFeatureForm
from ..forms.multiple_images_information_form import MultipleImagesInformationForm
from ..presenters import LastKnownMammogramPresenter
from ..presenters.medical_information_presenter import MedicalInformationPresenter
from .mixins import AppointmentMixin, InProgressAppointmentMixin, WorkflowSidebarMixin

MAMMOGRAMS_RECORD_MEDICAL_INFORMATION_VIEWNAME = "mammograms:record_medical_information"
APPOINTMENT_NOT_FOUND = "Appointment not found"
SHOW_APPOINTMENT_URL_NAME = "mammograms:show_appointment"
WorkflowSteps = AppointmentWorkflowStepCompletion.StepNames

logger = logging.getLogger(__name__)


class ConfirmIdentityView(WorkflowSidebarMixin, TemplateView):
    active_workflow_step = AppointmentWorkflowStepCompletion.StepNames.CONFIRM_IDENTITY
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

            logger.info(f"Confirmed identity for {self.request.user.pk}")
        else:
            logger.info(f"Identity already confirmed for user {self.request.user.pk}")

        return redirect(MAMMOGRAMS_RECORD_MEDICAL_INFORMATION_VIEWNAME, pk=pk)


class MedicalInformationView(WorkflowSidebarMixin, FormView):
    active_workflow_step = (
        AppointmentWorkflowStepCompletion.StepNames.REVIEW_MEDICAL_INFORMATION
    )
    template_name = "mammograms/record_medical_information.jinja"
    form_class = RecordMedicalInformationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        participant = self.participant
        last_confirmed_mammogram = participant.last_confirmed_mammogram
        reported_mammograms = self.appointment.recent_reported_mammograms(
            since_date=(
                last_confirmed_mammogram.exact_date
                if last_confirmed_mammogram
                else None
            )
        )

        presented_mammograms = LastKnownMammogramPresenter(
            self.request.user,
            reported_mammograms=reported_mammograms,
            last_confirmed_mammogram=last_confirmed_mammogram,
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
                WorklistItemService.create(self.appointment)
        except (IntegrityError, DatabaseError):
            messages.add_message(
                self.request,
                messages.INFO,
                "Unable to complete all sections. Please try again.",
            )
            return redirect(
                MAMMOGRAMS_RECORD_MEDICAL_INFORMATION_VIEWNAME,
                pk=self.appointment.pk,
            )
        except GatewayActionAlreadyExistsError as e:
            logger.warning(str(e))

        if gateway_images_enabled(self.appointment):
            return redirect("mammograms:gateway_images", pk=self.appointment.pk)

        return redirect("mammograms:take_images", pk=self.appointment.pk)


class AppointmentCannotGoAheadView(InProgressAppointmentMixin, FormView):
    active_workflow_step = AppointmentWorkflowStepCompletion.StepNames.CONFIRM_IDENTITY
    template_name = "mammograms/appointment_cannot_go_ahead.jinja"
    form_class = AppointmentCannotGoAheadForm

    def get_success_url(self):
        return reverse(
            "clinics:show_clinic", kwargs={"pk": self.appointment.clinic_slot.clinic.pk}
        )

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
                "presented_appointment": AppointmentPresenter(self.appointment),
                "return_url": extract_relative_redirect_url(self.request),
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

        participant = instance.screening_episode.participant
        escaped_name = escape(participant.full_name)
        view_appointment_url = reverse(
            "mammograms:show_appointment", kwargs={"pk": instance.pk}
        )
        view_link = f' <a href="{view_appointment_url}" class="app-u-nowrap">View their appointment</a>'
        if form.cleaned_data["decision"] == "True":
            message_text = (
                f"Appointment cancelled and a reschedule request has been"
                f" submitted for {escaped_name}.{view_link}"
            )
        else:
            message_text = (
                f"Appointment cancelled. {escaped_name} will be invited to"
                f" their next routine appointment.{view_link}"
            )
        messages.add_message(
            self.request,
            messages.SUCCESS,
            mark_safe(
                f'<p class="nhsuk-notification-banner__heading">{message_text}</p>'
            ),
        )
        return super().form_valid(form)


class ImagesView(WorkflowSidebarMixin, FormView):
    active_workflow_step = AppointmentWorkflowStepCompletion.StepNames.TAKE_IMAGES
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


class GatewayImagesView(WorkflowSidebarMixin, FormView):
    active_workflow_step = AppointmentWorkflowStepCompletion.StepNames.TAKE_IMAGES
    template_name = "mammograms/gateway_images.jinja"
    form_class = GatewayImageDetailsForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        images = get_images_for_appointment(self.appointment)
        title = "Image transfer in progress"

        context.update(
            {
                "heading": title,
                "page_title": title,
                "images": DicomStudyService.images_by_laterality_and_view(images),
                "image_count": len(images),
                "appointment_pk": self.appointment.pk,
                "continue_button_text": "Confirm all images received",
                "form_container_classes": "nhsuk-grid-column-full",
            }
        )
        return context

    @transaction.atomic
    def form_valid(self, form):
        form.save(
            DicomStudyService(
                appointment=self.appointment, current_user=self.request.user
            ),
            RecallService(appointment=self.appointment, current_user=self.request.user),
        )

        study = DicomStudy.for_appointment(self.appointment)

        if study.has_series_with_multiple_images():
            return redirect(
                "mammograms:add_multiple_images_information", pk=self.appointment_pk
            )
        else:
            self.mark_workflow_step_complete()
            return redirect("mammograms:check_information", pk=self.appointment_pk)

    def mark_workflow_step_complete(self):
        self.appointment.completed_workflow_steps.get_or_create(
            step_name=AppointmentWorkflowStepCompletion.StepNames.TAKE_IMAGES,
            defaults={"created_by": self.request.user},
        )


class AddMultipleImagesInformationView(WorkflowSidebarMixin, FormView):
    active_workflow_step = AppointmentWorkflowStepCompletion.StepNames.TAKE_IMAGES
    form_class = MultipleImagesInformationForm
    template_name = "mammograms/multiple_images_information.jinja"

    def get_study(self):
        try:
            if gateway_images_enabled(self.appointment):
                return DicomStudy.for_appointment(self.appointment)
            else:
                return self.appointment.study
        except Study.DoesNotExist:
            return None

    @cached_property
    def series_with_multiple_images(self):
        study = self.get_study()
        if not study:
            return []
        return list(study.series_with_multiple_images())

    def get(self, request, *args, **kwargs):
        if not self.series_with_multiple_images:
            return redirect(self.get_success_url())
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not self.series_with_multiple_images:
            return redirect(self.get_success_url())

        # Create a temporary form to check staleness using submitted data
        form = self.form_class(request.POST, instance=self.get_study())
        if form.is_stale():
            messages.add_message(
                request,
                messages.INFO,
                "The image details have changed. Please review and continue.",
            )
            return redirect(self.get_redirect_back_url())

        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.get_study()
        return kwargs

    def get_success_url(self):
        return reverse(
            "mammograms:check_information", kwargs={"pk": self.appointment.pk}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        title = (
            "Image transfer in progress"
            if gateway_images_enabled(self.appointment)
            else "Add image information"
        )

        context.update(
            {
                "heading": title,
                "page_title": title,
                "back_link_params": {"href": self.get_redirect_back_url()},
            },
        )
        return context

    def get_redirect_back_url(self):
        if gateway_images_enabled(self.appointment):
            return reverse(
                "mammograms:gateway_images", kwargs={"pk": self.appointment_pk}
            )
        else:
            return reverse(
                "mammograms:add_image_details", kwargs={"pk": self.appointment_pk}
            )

    @transaction.atomic
    def form_valid(self, form):
        form.update(self.study_service)

        auditor = Auditor.from_request(self.request)
        auditor.audit_bulk_update(form.series_list)

        self.mark_workflow_step_complete()
        return redirect(self.get_success_url())

    def mark_workflow_step_complete(self):
        self.appointment.completed_workflow_steps.get_or_create(
            step_name=AppointmentWorkflowStepCompletion.StepNames.TAKE_IMAGES,
            defaults={"created_by": self.request.user},
        )

    @property
    def study_service(self):
        if gateway_images_enabled(self.appointment):
            return DicomStudyService(self.appointment, self.request.user)
        else:
            return StudyService(self.appointment, self.request.user)


class BreastFeaturesView(InProgressAppointmentMixin, FormView):
    template_name = "mammograms/medical_information/breast_features/form.jinja"
    active_workflow_step = (
        AppointmentWorkflowStepCompletion.StepNames.REVIEW_MEDICAL_INFORMATION
    )

    def get_form(self):
        if hasattr(self.appointment, "breast_features"):
            form_class = UpdateBreastFeatureForm
        else:
            form_class = AddBreastFeatureForm

        return form_class(appointment=self.appointment, **self.get_form_kwargs())

    def get_context_data(self, **kwargs):
        if hasattr(self.appointment, "breast_features"):
            features = self.appointment.breast_features.annotations_json
        else:
            features = []

        context = super().get_context_data(**kwargs)
        context.update(
            {
                "heading": "Record breast features",
                "caption": self.participant.full_name,
                "page_title": "Record breast features",
                "features": features,
                "diagram_version": 1,
                "back_link_params": {
                    "href": reverse(
                        "mammograms:record_medical_information",
                        kwargs={"pk": self.appointment_pk},
                    )
                },
                "cannot_proceed_url": reverse(
                    "mammograms:appointment_cannot_go_ahead",
                    kwargs={"pk": self.appointment_pk},
                ),
            }
        )
        return context

    def form_valid(self, form):
        form.save(current_user=self.request.user)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "mammograms:record_medical_information",
            kwargs={"pk": self.appointment_pk},
        )


@require_http_methods(["GET", "POST"])
def check_in(request, pk):
    if request.method == "GET":
        return redirect("mammograms:show_appointment", pk=pk)

    try:
        provider = request.user.current_provider
        appointment = provider.appointments.get(pk=pk)
    except Appointment.DoesNotExist:
        raise Http404("Appointment not found")

    if _should_redirect_stale_check_in(request, appointment):
        messages.add_message(
            request,
            messages.INFO,
            f"{appointment.participant.full_name} has already been checked in.",
        )
        return redirect("clinics:show_clinic", pk=appointment.clinic_slot.clinic.pk)

    AppointmentStatusUpdater(
        appointment=appointment, current_user=request.user
    ).check_in()

    if request.accepts("text/html"):
        return redirect("mammograms:show_appointment", pk=pk)
    else:
        return HttpResponse(status=201)


def _should_redirect_stale_check_in(request, appointment):
    machine = AppointmentMachine.from_appointment(appointment)
    current_status = appointment.current_status
    checked_in_by_current_user = (
        current_status.name == AppointmentStatusNames.CHECKED_IN
        and current_status.created_by == request.user
    )
    # Don't redirect if it's a valid state transition, or if the same user is re-submitting
    # the check-in (e.g. due to a double form submission). Redirect in all other cases,
    # which would indicate a stale form submission.
    return not machine.can("check_in") and not checked_in_by_current_user


@require_http_methods(["GET", "POST"])
@permission_required(Permission.DO_MAMMOGRAM_APPOINTMENT, raise_exception=True)
def start_appointment(request, pk):
    if request.method == "GET":
        return redirect("mammograms:show_appointment", pk=pk)

    try:
        provider = request.user.current_provider
        appointment = provider.appointments.get(pk=pk)
    except Appointment.DoesNotExist:
        raise Http404("Appointment not found")

    if not AppointmentMachine.from_appointment(appointment).can("start"):
        patient_name = appointment.participant.full_name
        started_by = appointment.current_status.created_by.get_short_name()
        messages.add_message(
            request,
            messages.WARNING,
            f"Appointment for {patient_name} has already been started by {started_by}.",
        )
        return redirect(
            "clinics:list_clinic_appointments_in_progress",
            pk=appointment.clinic_slot.clinic.pk,
        )

    AppointmentStatusUpdater(appointment=appointment, current_user=request.user).start()

    if request.accepts("text/html"):
        return redirect("mammograms:confirm_identity", pk=pk)
    else:
        return HttpResponse(status=201)


@require_http_methods(["GET", "POST"])
@permission_required(Permission.DO_MAMMOGRAM_APPOINTMENT, raise_exception=True)
def resume_appointment(request, pk):
    if request.method == "GET":
        return redirect("mammograms:show_appointment", pk=pk)

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
            if gateway_images_enabled(appointment):
                next_step = "mammograms:gateway_images"
            else:
                next_step = "mammograms:take_images"
        else:
            next_step = "mammograms:record_medical_information"

    return redirect(next_step, pk=pk)


class PauseAppointmentView(InProgressAppointmentMixin, FormView):
    active_workflow_step = AppointmentWorkflowStepCompletion.StepNames.CONFIRM_IDENTITY
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
            raise ValidationError(
                f"Can only be paused by {appointment.current_status.created_by.get_full_name()}"
            )

        AppointmentStatusUpdater(
            appointment=appointment, current_user=self.request.user
        ).pause()

        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "clinics:list_clinic_appointments_in_progress",
            kwargs={"pk": self.appointment.clinic_slot.clinic.pk},
        )


class MarkSectionReviewedView(InProgressAppointmentMixin, View):
    active_workflow_step = (
        AppointmentWorkflowStepCompletion.StepNames.REVIEW_MEDICAL_INFORMATION
    )

    def get(self, request, *args, **kwargs):
        return redirect(
            MAMMOGRAMS_RECORD_MEDICAL_INFORMATION_VIEWNAME, pk=self.appointment.pk
        )

    def post(self, request, *args, **kwargs):
        section = kwargs.get("section")

        valid_sections = [choice[0] for choice in MedicalInformationSection.choices]
        if section not in valid_sections:
            raise Http404("Invalid section")

        existing_review = self.appointment.medical_information_reviews.filter(
            section=section
        ).first()

        if self.request.accepts("text/html"):
            return self._handle_html(request, section, existing_review)
        else:
            return self._handle_plain(request, section, existing_review)

    def _handle_html(self, request, section, existing_review):
        if existing_review:
            if existing_review.reviewed_by != request.user:
                messages.add_message(
                    request,
                    messages.INFO,
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

    def _handle_plain(self, request, section, existing_review):
        if existing_review:
            return HttpResponse(status=409)
        else:
            self.appointment.medical_information_reviews.create(
                section=section,
                reviewed_by=request.user,
            )
            return HttpResponse(status=201)


@require_http_methods(["GET"])
@permission_required(Permission.DO_MAMMOGRAM_APPOINTMENT, raise_exception=True)
def appointment_should_not_proceed(
    request, appointment_pk, participant_reported_mammogram_pk
):
    provider = request.user.current_provider
    try:
        appointment = provider.appointments.select_related(
            "clinic_slot__clinic",
            "screening_episode__participant",
            "screening_episode__participant__address",
        ).get(pk=appointment_pk)
    except Appointment.DoesNotExist:
        raise Http404(APPOINTMENT_NOT_FOUND)

    try:
        mammogram = appointment.reported_mammograms.get(
            pk=participant_reported_mammogram_pk
        )
    except ParticipantReportedMammogram.DoesNotExist:
        raise Http404("Participant reported mammogram not found")

    return_url = extract_relative_redirect_url(request, default="")
    update_previous_mammogram_url = (
        reverse(
            "mammograms:update_previous_mammogram",
            kwargs={
                "pk": appointment_pk,
                "participant_reported_mammogram_pk": participant_reported_mammogram_pk,
            },
        )
        + "?"
        + urlencode({"return_url": return_url})
    )
    proceed_anyway_url = (
        reverse(
            "mammograms:proceed_anyway",
            kwargs={
                "pk": appointment_pk,
                "participant_reported_mammogram_pk": participant_reported_mammogram_pk,
            },
        )
        + "?"
        + urlencode({"return_url": return_url})
    )
    relative_date = (
        format_relative_date(mammogram.exact_date)
        if mammogram.exact_date
        else "less than 6 months ago"
    )
    return render(
        request,
        "mammograms/appointment_should_not_proceed.jinja",
        {
            "caption": appointment.screening_episode.participant.full_name,
            "page_title": "This appointment should not proceed",
            "heading": "This appointment should not proceed",
            "back_link_params": {
                "href": update_previous_mammogram_url,
            },
            "presented_appointment": AppointmentPresenter(appointment),
            "time_since_previous_mammogram": relative_date,
            "update_previous_mammogram_url": update_previous_mammogram_url,
            "proceed_anyway_url": proceed_anyway_url,
            "return_url": return_url,
        },
    )


class AppointmentProceedAnywayView(
    AppointmentMixin, UpdateWithAuditView, PermissionRequiredMixin
):
    form_class = AppointmentProceedAnywayForm
    template_name = "mammograms/proceed_anyway.jinja"
    thing_name = "a previous mammogram"
    permission_required = Permission.DO_MAMMOGRAM_APPOINTMENT
    raise_exception = True

    def update_title(self, thing_name):
        return "You are continuing despite a recent mammogram"

    def get_object(self):
        return get_object_or_none(
            self.appointment.reported_mammograms,
            pk=self.kwargs.get("participant_reported_mammogram_pk"),
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["participant"] = self.appointment.participant
        return kwargs

    def get_success_url(self):
        return extract_relative_redirect_url(
            self.request,
            default=reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": self.appointment.pk},
            ),
        )

    def get_back_link_params(self):
        return_url = self.get_success_url()

        return {
            "href": reverse(
                "mammograms:appointment_should_not_proceed",
                kwargs={
                    "appointment_pk": self.appointment.pk,
                    "participant_reported_mammogram_pk": self.kwargs[
                        "participant_reported_mammogram_pk"
                    ],
                },
            )
            + "?"
            + urlencode({"return_url": return_url}),
            "text": "Back",
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        participant = self.appointment.participant

        context.update(
            {
                "back_link_params": self.get_back_link_params(),
                "caption": participant.full_name,
                "participant_first_name": participant.first_name,
                "return_url": self.get_success_url(),
            },
        )

        return context


@require_http_methods(["GET"])
@permission_required(Permission.DO_MAMMOGRAM_APPOINTMENT, raise_exception=True)
def check_information(request, pk):
    provider = request.user.current_provider
    try:
        appointment = provider.appointments.select_related(
            "clinic_slot__clinic",
            "screening_episode__participant",
            "screening_episode__participant__address",
        ).get(pk=pk)
    except Appointment.DoesNotExist:
        raise Http404("Appointment not found")

    if not AppointmentWorkflowService(appointment, request.user).is_valid_next_step(
        StepNames.CHECK_INFORMATION
    ):
        return redirect(
            SHOW_APPOINTMENT_URL_NAME,
            pk=appointment.pk,
        )

    return render(
        request,
        "mammograms/check_information.jinja",
        context={
            "page_title": "Check information",
            "heading": "Check information",
            "presented_appointment": AppointmentPresenter(appointment),
            "presented_images": ImagesPresenterFactory.presenter_for(appointment),
            "presented_medical_information": CheckMedicalInformationPresenter(
                appointment
            ),
            "presented_workflow_steps": WorkflowPresenter(
                AppointmentWorkflowService(appointment, request.user)
            ).workflow_steps(StepNames.CHECK_INFORMATION),
        },
    )


@require_http_methods(["POST"])
@permission_required(Permission.DO_MAMMOGRAM_APPOINTMENT, raise_exception=True)
def complete_screening(request, pk):
    provider = request.user.current_provider
    try:
        appointment = provider.appointments.select_related(
            "clinic_slot__clinic",
            "screening_episode__participant",
        ).get(pk=pk)
    except Appointment.DoesNotExist:
        raise Http404(APPOINTMENT_NOT_FOUND)

    if not AppointmentWorkflowService(appointment, request.user).is_valid_next_step(
        StepNames.CHECK_INFORMATION
    ):
        return redirect(
            SHOW_APPOINTMENT_URL_NAME,
            pk=appointment.pk,
        )

    AppointmentStatusUpdater(
        appointment=appointment, current_user=request.user
    ).screen()
    appointment.completed_workflow_steps.create(
        step_name=StepNames.CHECK_INFORMATION,
        created_by=request.user,
    )

    view_appointment_url = reverse(
        SHOW_APPOINTMENT_URL_NAME,
        kwargs={
            "pk": appointment.pk,
        },
    )
    escaped_full_name = escape(appointment.screening_episode.participant.full_name)
    messages.add_message(
        request,
        messages.SUCCESS,
        mark_safe(
            f"""
            <p class=\"nhsuk-notification-banner__heading\">
                {escaped_full_name} has been screened.
                <a href=\"{view_appointment_url}\" class=\"app-u-nowrap\">
                    View their appointment
                </a>
            </p>
            """
        ),
    )

    return redirect("clinics:show_clinic", pk=appointment.clinic_slot.clinic.pk)


@require_http_methods(["POST"])
@permission_required(Permission.DO_MAMMOGRAM_APPOINTMENT, raise_exception=True)
def attended_not_screened(request, appointment_pk):
    provider = request.user.current_provider
    try:
        appointment = provider.appointments.get(pk=appointment_pk)
    except Appointment.DoesNotExist:
        raise Http404(APPOINTMENT_NOT_FOUND)

    AppointmentStatusUpdater(
        appointment, current_user=request.user
    ).mark_attended_not_screened()

    return redirect("clinics:show_clinic", pk=appointment.clinic_slot.clinic.pk)


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
                    {
                        "images": DicomStudyService.images_by_laterality_and_view(
                            images
                        ),
                        "image_count": len(images),
                    },
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
