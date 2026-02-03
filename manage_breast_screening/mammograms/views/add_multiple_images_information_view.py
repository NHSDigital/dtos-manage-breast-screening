import logging
from functools import cached_property

from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import FormView

from manage_breast_screening.core.services.auditor import Auditor
from manage_breast_screening.mammograms.views.mixins import InProgressAppointmentMixin
from manage_breast_screening.manual_images.models import Study
from manage_breast_screening.participants.models.appointment import (
    AppointmentWorkflowStepCompletion,
)

from ..forms.multiple_images_information_form import MultipleImagesInformationForm

logger = logging.getLogger(__name__)


class AddMultipleImagesInformationView(InProgressAppointmentMixin, FormView):
    form_class = MultipleImagesInformationForm
    template_name = "mammograms/multiple_images_information.jinja"

    def get_study(self):
        try:
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
        current_series = list(self.series_with_multiple_images)
        if not current_series:
            return redirect(self.get_success_url())

        # Create a temporary form to check staleness using submitted data
        form = self.form_class(
            request.POST, series_list=current_series, instance=self.get_study()
        )
        if form.is_stale(current_series):
            messages.add_message(
                request,
                messages.WARNING,
                "The image details have changed. Please review and continue.",
            )
            return redirect(
                reverse(
                    "mammograms:add_image_details",
                    kwargs={"pk": self.appointment_pk},
                )
            )

        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["series_list"] = self.series_with_multiple_images
        kwargs["instance"] = self.get_study()
        return kwargs

    def get_success_url(self):
        return reverse(
            "mammograms:check_information", kwargs={"pk": self.appointment.pk}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "heading": "Add image information",
                "page_title": "Add image information",
                "back_link_params": {
                    "href": reverse(
                        "mammograms:add_image_details",
                        kwargs={"pk": self.appointment_pk},
                    ),
                },
            },
        )
        return context

    @transaction.atomic
    def form_valid(self, form):
        form.update()

        auditor = Auditor.from_request(self.request)
        auditor.audit_bulk_update(form.series_list)

        self.mark_workflow_step_complete()
        return redirect(self.get_success_url())

    def mark_workflow_step_complete(self):
        self.appointment.completed_workflow_steps.get_or_create(
            step_name=AppointmentWorkflowStepCompletion.StepNames.TAKE_IMAGES,
            defaults={"created_by": self.request.user},
        )
