from django.contrib import messages
from django.urls import reverse
from django.views.generic import FormView

from manage_breast_screening.mammograms.forms.benign_lump_history_item_form import (
    BenignLumpHistoryItemForm,
)

from .mixins import InProgressAppointmentMixin


class AddBenignLumpHistoryItemView(InProgressAppointmentMixin, FormView):
    form_class = BenignLumpHistoryItemForm
    template_name = "mammograms/medical_information/medical_history/forms/benign_lump_history_item_form.jinja"

    def form_valid(self, form):
        form.create(appointment=self.appointment, request=self.request)

        messages.add_message(
            self.request,
            messages.SUCCESS,
            "Benign lump history added",
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
                "participant_first_name": participant.first_name,
                "heading": "Add details of benign lumps",
                "page_title": "Add details of benign lumps",
            },
        )

        return context
