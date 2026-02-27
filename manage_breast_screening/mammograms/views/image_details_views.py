import logging

from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import FormView

from manage_breast_screening.mammograms.services.appointment_services import (
    RecallService,
)
from manage_breast_screening.mammograms.views.mixins import InProgressAppointmentMixin
from manage_breast_screening.manual_images.services import StudyService
from manage_breast_screening.participants.models.appointment import (
    AppointmentWorkflowStepCompletion,
)

from ..forms.images.image_details_form import ImageDetailsForm

logger = logging.getLogger(__name__)


class AddImageDetailsView(InProgressAppointmentMixin, FormView):
    form_class = ImageDetailsForm
    template_name = "mammograms/image_details.jinja"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "heading": "Provide image details",
                "page_title": "Provide image details",
                "back_link_params": {
                    "href": reverse(
                        "mammograms:take_images",
                        kwargs={"pk": self.appointment_pk},
                    )
                },
            }
        )
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = getattr(self.appointment, "study", None)
        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        study = form.save(
            StudyService(appointment=self.appointment, current_user=self.request.user),
            RecallService(appointment=self.appointment, current_user=self.request.user),
        )

        if study.has_series_with_multiple_images():
            return redirect(
                "mammograms:add_multiple_images_information", pk=self.appointment_pk
            )

        self.mark_workflow_step_complete()
        return redirect("mammograms:check_information", pk=self.appointment_pk)

    def mark_workflow_step_complete(self):
        self.appointment.completed_workflow_steps.get_or_create(
            step_name=AppointmentWorkflowStepCompletion.StepNames.TAKE_IMAGES,
            defaults={"created_by": self.request.user},
        )


class UpdateImageDetailsView(InProgressAppointmentMixin, FormView):
    form_class = ImageDetailsForm
    template_name = "mammograms/image_details.jinja"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "heading": "Edit image details",
                "page_title": "Edit image details",
                "back_link_params": reverse(
                    "mammograms:take_images",
                    kwargs={"pk": self.appointment_pk},
                ),
            }
        )
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = getattr(self.appointment, "study", None)
        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        study = form.save(
            StudyService(appointment=self.appointment, current_user=self.request.user),
            RecallService(appointment=self.appointment, current_user=self.request.user),
        )

        if study.has_series_with_multiple_images():
            return redirect(
                "mammograms:add_multiple_images_information", pk=self.appointment_pk
            )

        return redirect("mammograms:check_information", pk=self.appointment_pk)
