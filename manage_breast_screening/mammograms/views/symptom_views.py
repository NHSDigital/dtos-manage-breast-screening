from functools import cached_property

from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import FormView

from manage_breast_screening.participants.models.symptom import Symptom

from ..forms.symptom_forms import LumpForm
from .mixins import InProgressAppointmentMixin


class AddOrChangeLump(InProgressAppointmentMixin, FormView):
    """
    Add or change a symptom: lump
    """

    form_class = LumpForm
    template_name = "mammograms/medical_information/symptoms/lump.jinja"

    @cached_property
    def participant(self):
        return self.appointment.participant

    @cached_property
    def is_update(self):
        return "lump_pk" in self.kwargs

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        if self.is_update:
            instance = get_object_or_404(
                Symptom, pk=self.kwargs["lump_pk"], appointment_id=self.kwargs["pk"]
            )
            kwargs["instance"] = instance

        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        context.update(
            {
                "back_link_params": {
                    "href": reverse(
                        "mammograms:record_medical_information",
                        kwargs={"pk": self.appointment_pk},
                    ),
                    "text": "Back to appointment",
                },
                "caption": self.participant.full_name,
                "heading": "Details of the lump",
            },
        )

        return context

    def form_valid(self, form):
        if self.is_update:
            form.update(request=self.request)
        else:
            form.create(appointment=self.appointment, request=self.request)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "mammograms:record_medical_information", kwargs={"pk": self.appointment.pk}
        )
