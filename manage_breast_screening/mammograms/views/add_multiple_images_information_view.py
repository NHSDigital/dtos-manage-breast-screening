import logging
from functools import cached_property

from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import FormView

from manage_breast_screening.core.services.auditor import Auditor
from manage_breast_screening.dicom.models import Study as DicomStudy
from manage_breast_screening.dicom.study_service import (
    StudyService as DicomStudyService,
)
from manage_breast_screening.mammograms.views import gateway_images_enabled
from manage_breast_screening.mammograms.views.mixins import (
    WorkflowSidebarMixin,
)
from manage_breast_screening.manual_images.models import Study
from manage_breast_screening.manual_images.services import StudyService
from manage_breast_screening.participants.models.appointment import (
    AppointmentWorkflowStepCompletion,
)

from ..forms.multiple_images_information_form import MultipleImagesInformationForm

logger = logging.getLogger(__name__)


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
