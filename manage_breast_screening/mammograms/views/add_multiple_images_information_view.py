import logging
from functools import cached_property

from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse

from manage_breast_screening.core.views.generic import UpdateWithAuditView
from manage_breast_screening.mammograms.views.mixins import InProgressAppointmentMixin
from manage_breast_screening.manual_images.models import Study
from manage_breast_screening.participants.models.appointment import (
    AppointmentWorkflowStepCompletion,
)

from ..forms.multiple_images_information_form import MultipleImagesInformationForm

logger = logging.getLogger(__name__)


class AddMultipleImagesInformationView(InProgressAppointmentMixin, UpdateWithAuditView):
    form_class = MultipleImagesInformationForm
    template_name = "mammograms/multiple_images_information.jinja"
    thing_name = "image information"
    model = Study

    def update_title(self, thing_name):
        return "Add image information"

    def get_object(self, queryset=None):
        return Study.objects.filter(appointment=self.appointment).first()

    @cached_property
    def series_with_multiple_images(self):
        study = self.get_object()
        if not study:
            return []
        return list(
            study.series_set.filter(count__gt=1).order_by("laterality", "view_position")
        )

    def get(self, request, *args, **kwargs):
        if not self.series_with_multiple_images:
            return redirect(self.get_success_url())
        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["series_list"] = self.series_with_multiple_images
        return kwargs

    def get_success_url(self):
        return reverse(
            "mammograms:check_information", kwargs={"pk": self.appointment.pk}
        )

    def get_back_link_params(self):
        return {
            "href": reverse(
                "mammograms:add_image_details",
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

    @transaction.atomic
    def form_valid(self, form):
        response = super().form_valid(form)
        self.mark_workflow_step_complete()
        return response

    def mark_workflow_step_complete(self):
        self.appointment.completed_workflow_steps.get_or_create(
            step_name=AppointmentWorkflowStepCompletion.StepNames.TAKE_IMAGES,
            defaults={"created_by": self.request.user},
        )

    def should_add_message(self, form) -> bool:
        return False
