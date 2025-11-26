from django.contrib import messages
from django.urls import reverse
from django.views.generic import FormView

from ..forms.breast_augmentation_history_form import BreastAugmentationHistoryForm
from .mixins import InProgressAppointmentMixin


class AddBreastAugmentationHistoryView(InProgressAppointmentMixin, FormView):
    form_class = BreastAugmentationHistoryForm
    template_name = "mammograms/medical_information/medical_history/forms/breast_augmentation_history.jinja"

    def get_success_url(self):
        return reverse(
            "mammograms:record_medical_information", kwargs={"pk": self.appointment.pk}
        )

    def form_valid(self, form):
        form.create(appointment=self.appointment, request=self.request)

        messages.add_message(
            self.request,
            messages.SUCCESS,
            "Details of breast implants or augmentation added",
        )

        return super().form_valid(form)

    def get_back_link_params(self):
        return {
            "href": reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": self.appointment_pk},
            ),
            "text": "Back to appointment",
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        participant = self.appointment.participant

        context.update(
            {
                "back_link_params": self.get_back_link_params(),
                "caption": participant.full_name,
                "participant_first_name": participant.first_name,
                "heading": "Add details of breast implants or augmentation",
                "page_title": "Add details of breast implants or augmentation",
            },
        )

        return context
