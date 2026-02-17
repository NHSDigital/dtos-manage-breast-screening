from django.urls import reverse
from django.views.generic import FormView

from ..forms.breast_feature_form import CreateBreastFeatureForm, UpdateBreastFeatureForm
from .mixins import InProgressAppointmentMixin


class RecordBreastFeaturesView(InProgressAppointmentMixin, FormView):
    template_name = "mammograms/record_breast_features.jinja"

    def get_form(self):
        if hasattr(self.appointment, "breast_features"):
            form_class = UpdateBreastFeatureForm
        else:
            form_class = CreateBreastFeatureForm

        return form_class(appointment=self.appointment, **self.get_form_kwargs())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "heading": "Record breast features",
                "page_title": "Record breast features",
                "diagram_version": 1,
                "back_link_params": reverse(
                    "mammograms:record_medical_information",
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
