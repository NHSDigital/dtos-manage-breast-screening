from functools import cached_property

from django.urls import reverse
from django.views.generic import FormView

from manage_breast_screening.core.services.auditor import Auditor

from ..forms.symptom_forms import LumpForm
from .mixins import InProgressAppointmentMixin


class AddLump(InProgressAppointmentMixin, FormView):
    """
    Add a symptom: lump
    """

    form_class = LumpForm
    template_name = "mammograms/medical_information/symptoms/lump.jinja"

    @cached_property
    def participant(self):
        return self.appointment.participant

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        context.update(
            {
                "back_link_params": {
                    "href": reverse(
                        "mammograms:start_screening", kwargs={"pk": self.appointment_pk}
                    ),
                    "text": "Back to appointment",
                },
                "caption": self.participant.full_name,
                "heading": "Details of the lump",
            },
        )

        return context

    def form_valid(self, form):
        symptom = form.save(appointment=self.appointment)
        Auditor.from_request(self.request).audit_create(symptom)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "mammograms:record_medical_information", kwargs={"pk": self.appointment.pk}
        )
