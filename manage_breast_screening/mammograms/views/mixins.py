from functools import cached_property

from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from rules.contrib.views import PermissionRequiredMixin

from manage_breast_screening.auth.models import Permission
from manage_breast_screening.mammograms.presenters.appointment_presenters import (
    AppointmentPresenter,
    WorkflowPresenter,
)
from manage_breast_screening.mammograms.services.appointment_services import (
    AppointmentWorkflowService,
)
from manage_breast_screening.participants.models import Appointment
from manage_breast_screening.participants.models.appointment import (
    AppointmentWorkflowStepCompletion,
)


class AppointmentMixin:
    """
    A view mixin that exposes the appointment.
    """

    @property
    def appointment_pk(self):
        return self.kwargs["pk"]

    @cached_property
    def appointment(self):
        provider = self.request.user.current_provider
        try:
            return provider.appointments.select_related(
                "clinic_slot__clinic",
                "screening_episode__participant",
                "screening_episode__participant__address",
            ).get(pk=self.appointment_pk)
        except Appointment.DoesNotExist:
            raise Http404

    @cached_property
    def participant(self):
        return self.appointment.participant

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "presented_appointment": AppointmentPresenter(self.appointment),
            },
        )

        return context


class AppointmentTabMixin(AppointmentMixin):
    """
    A view that by the tabs on the appointment page.
    If the appointment is in progress with another user then display a message.
    """

    def dispatch(self, request, *args, **kwargs):
        current_status = self.appointment.current_status
        if (
            current_status.is_in_progress()
            and self.request.user.nhs_uid != current_status.created_by.nhs_uid
        ):
            messages.add_message(
                request,
                messages.INFO,
                f"This appointment is currently being run by {current_status.created_by.get_short_name()}.",
            )
        return super().dispatch(request, *args, **kwargs)


class InProgressAppointmentMixin(PermissionRequiredMixin, AppointmentMixin):
    """
    A view that is only shown with in progress appointments.
    If the appointment is not in progress, redirect to the appointment show page.
    """

    permission_required = Permission.DO_MAMMOGRAM_APPOINTMENT
    raise_exception = True
    active_workflow_step = None

    def dispatch(self, request, *args, **kwargs):
        appointment = self.appointment  # type: ignore
        if not appointment.current_status.is_in_progress_with(request.user):
            return redirect(
                "mammograms:show_appointment",
                pk=appointment.pk,
            )

        if not self.active_workflow_step:
            raise ValueError(
                f"active_workflow_step must be set on WorkflowSidebarMixin {self.__class__.__name__}"
            )

        if not AppointmentWorkflowService(
            self.appointment, self.request.user
        ).is_valid_next_step(self.active_workflow_step):
            return redirect(
                "mammograms:show_appointment",
                pk=self.appointment.pk,
            )

        return super().dispatch(request, *args, **kwargs)  # type: ignore


class MedicalInformationMixin(InProgressAppointmentMixin):
    """
    Mixin for views that hang off the medical information page.

    These all follow a similar structure, and have the same onwards / back
    navigation.
    """

    active_workflow_step = (
        AppointmentWorkflowStepCompletion.StepNames.REVIEW_MEDICAL_INFORMATION
    )

    def get_success_url(self):
        return reverse(
            "mammograms:record_medical_information", kwargs={"pk": self.appointment.pk}
        )

    def get_back_link_params(self):
        return {
            "href": reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": self.appointment_pk},
            ),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        participant = self.appointment.participant

        context.update(
            {
                "back_link_params": self.get_back_link_params(),
                "caption": participant.full_name,
                "participant_first_name": participant.first_name,
            },
        )

        return context


class WorkflowSidebarMixin(InProgressAppointmentMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["presented_workflow_steps"] = WorkflowPresenter(
            AppointmentWorkflowService(self.appointment, self.request.user)
        ).workflow_steps(self.active_workflow_step)

        return context
