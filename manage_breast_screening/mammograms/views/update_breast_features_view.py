from django.urls import reverse
from django.views.generic import FormView

from ..forms.breast_feature_form import AddBreastFeatureForm, UpdateBreastFeatureForm
from .mixins import InProgressAppointmentMixin


class UpdateBreastFeaturesView(InProgressAppointmentMixin, FormView):
    template_name = "mammograms/medical_information/breast_features/form.jinja"

    def get_form(self):
        if hasattr(self.appointment, "breast_features"):
            form_class = UpdateBreastFeatureForm
        else:
            form_class = AddBreastFeatureForm

        return form_class(appointment=self.appointment, **self.get_form_kwargs())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "heading": "Record breast features",
                "caption": self.participant.full_name,
                "page_title": "Record breast features",
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
