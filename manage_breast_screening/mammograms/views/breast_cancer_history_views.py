from django.contrib import messages
from django.urls import reverse
from django.views.generic import FormView

from manage_breast_screening.mammograms.forms.breast_cancer_history_form import (
    BreastCancerHistoryForm,
)

from .mixins import InProgressAppointmentMixin


class AddBreastCancerHistoryView(InProgressAppointmentMixin, FormView):
    form_class = BreastCancerHistoryForm
    template_name = "mammograms/medical_information/medical_history/forms/breast_cancer_history_item_form.jinja"

    def form_valid(self, form):
        form.create(appointment=self.appointment, request=self.request)

        messages.add_message(
            self.request,
            messages.SUCCESS,
            "Breast cancer history added",
        )

        return super().form_valid(form)

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
            "text": "Back",
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        participant = self.appointment.participant

        context.update(
            {
                "back_link_params": self.get_back_link_params(),
                "caption": participant.full_name,
                "heading": "Add details of breast cancer",
                "page_title": "Add details of breast cancer",
            },
        )

        return context
