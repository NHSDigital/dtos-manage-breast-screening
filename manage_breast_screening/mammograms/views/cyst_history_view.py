from functools import cached_property

from django.contrib import messages
from django.urls import reverse
from django.views.generic import FormView

from ..forms.cyst_history_form import (
    CystHistoryForm,
)
from .mixins import InProgressAppointmentMixin


class AddCystHistoryView(InProgressAppointmentMixin, FormView):
    form_class = CystHistoryForm
    template_name = (
        "mammograms/medical_information/medical_history/forms/cyst_history.jinja"
    )

    def get_success_url(self):
        return reverse(
            "mammograms:record_medical_information", kwargs={"pk": self.appointment.pk}
        )

    def form_valid(self, form):
        form.create(appointment=self.appointment, request=self.request)

        messages.add_message(
            self.request,
            messages.SUCCESS,
            "Details of cysts added",
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
                "heading": "Add details of cysts",
                "page_title": "Details of the cysts",
            },
        )

        return context

    @cached_property
    def participant(self):
        return self.appointment.participant

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["participant"] = self.participant
        return kwargs
