import logging

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_http_methods
from rules.contrib.views import PermissionRequiredMixin

from manage_breast_screening.auth.models import Permission
from manage_breast_screening.core.utils.date_formatting import format_relative_date
from manage_breast_screening.core.utils.relative_redirects import (
    extract_relative_redirect_url,
)
from manage_breast_screening.core.views.generic import UpdateWithAuditView
from manage_breast_screening.mammograms.presenters.appointment_presenters import (
    AppointmentPresenter,
    ImagesPresenterFactory,
)
from manage_breast_screening.mammograms.presenters.medical_history.check_medical_information_presenter import (
    CheckMedicalInformationPresenter,
)
from manage_breast_screening.mammograms.services.appointment_services import (
    AppointmentStatusUpdater,
)
from manage_breast_screening.mammograms.views.mixins import AppointmentMixin
from manage_breast_screening.participants.models import ParticipantReportedMammogram
from manage_breast_screening.participants.models.appointment import (
    Appointment,
    AppointmentWorkflowStepCompletion,
)

from ..forms.appointment_proceed_anyway_form import AppointmentProceedAnywayForm

APPOINTMENT_NOT_FOUND = "Appointment not found"

logger = logging.getLogger(__name__)


@permission_required(Permission.DO_MAMMOGRAM_APPOINTMENT)
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
    exact_date = mammogram.exact_date

    return_url = extract_relative_redirect_url(request, default="")
    change_previous_mammogram_url = (
        reverse(
            "mammograms:change_previous_mammogram",
            kwargs={
                "pk": appointment_pk,
                "participant_reported_mammogram_pk": participant_reported_mammogram_pk,
            },
        )
        + f"?return_url={return_url}"
    )
    proceed_anyway_url = (
        reverse(
            "mammograms:proceed_anyway",
            kwargs={
                "pk": appointment_pk,
                "participant_reported_mammogram_pk": participant_reported_mammogram_pk,
            },
        )
        + f"?return_url={return_url}"
    )
    return render(
        request,
        "mammograms/appointment_should_not_proceed.jinja",
        {
            "caption": appointment.screening_episode.participant.full_name,
            "page_title": "This appointment should not proceed",
            "heading": "This appointment should not proceed",
            "back_link_params": {
                "href": change_previous_mammogram_url,
            },
            "presented_appointment": AppointmentPresenter(appointment),
            "time_since_previous_mammogram": format_relative_date(exact_date),
            "change_previous_mammogram_url": change_previous_mammogram_url,
            "proceed_anyway_url": proceed_anyway_url,
            "return_url": return_url,
        },
    )


@require_http_methods(["POST"])
@permission_required(Permission.DO_MAMMOGRAM_APPOINTMENT)
def attended_not_screened(request, appointment_pk):
    provider = request.user.current_provider
    try:
        appointment = provider.appointments.get(pk=appointment_pk)
    except Appointment.DoesNotExist:
        raise Http404(APPOINTMENT_NOT_FOUND)

    AppointmentStatusUpdater(
        appointment, current_user=request.user
    ).mark_attended_not_screened()

    return redirect("clinics:show", pk=appointment.clinic_slot.clinic.pk)


class AppointmentProceedAnywayView(
    AppointmentMixin, UpdateWithAuditView, PermissionRequiredMixin
):
    form_class = AppointmentProceedAnywayForm
    template_name = "mammograms/proceed_anyway.jinja"
    thing_name = "a previous mammogram"
    permission_required = Permission.DO_MAMMOGRAM_APPOINTMENT

    def update_title(self, thing_name):
        return "You are continuing despite a recent mammogram"

    def get_object(self):
        try:
            return ParticipantReportedMammogram.objects.get(
                pk=self.kwargs["participant_reported_mammogram_pk"],
            )
        except ParticipantReportedMammogram.DoesNotExist:
            logger.exception(
                "ParticipantReportedMammogram does not exist for kwargs=%s", self.kwargs
            )
            return None

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
            + f"?return_url={return_url}",
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
@permission_required(Permission.DO_MAMMOGRAM_APPOINTMENT)
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
        },
    )


@require_http_methods(["POST"])
@permission_required(Permission.DO_MAMMOGRAM_APPOINTMENT)
def complete_screening(request, pk):
    provider = request.user.current_provider
    try:
        appointment = provider.appointments.select_related(
            "clinic_slot__clinic",
            "screening_episode__participant",
        ).get(pk=pk)
    except Appointment.DoesNotExist:
        raise Http404(APPOINTMENT_NOT_FOUND)

    AppointmentStatusUpdater(
        appointment=appointment, current_user=request.user
    ).screen()
    appointment.completed_workflow_steps.create(
        step_name=AppointmentWorkflowStepCompletion.StepNames.CHECK_INFORMATION,
        created_by=request.user,
    )

    view_appointment_url = reverse(
        "mammograms:show_appointment",
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

    return redirect("clinics:show", pk=appointment.clinic_slot.clinic.pk)
