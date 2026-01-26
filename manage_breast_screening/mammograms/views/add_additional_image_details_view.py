import logging

from django.urls import reverse

from manage_breast_screening.core.views.generic import (
    AddWithAuditView,
)
from manage_breast_screening.mammograms.views.mixins import (
    InProgressAppointmentMixin,
)

from ..forms.add_additional_image_details_form import (
    AddAdditionalImageDetailsForm,
)

logger = logging.getLogger(__name__)


class AddAdditionalImageDetailsView(InProgressAppointmentMixin, AddWithAuditView):
    form_class = AddAdditionalImageDetailsForm
    template_name = "mammograms/add_additional_image_details.jinja"
    thing_name = "image details"

    def add_title(self, thing_name):
        return "Provide image details"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["participant"] = self.participant
        return kwargs

    def get_create_kwargs(self):
        return {"appointment": self.appointment}

    def get_success_url(self):
        return reverse(
            "mammograms:check_information", kwargs={"pk": self.appointment.pk}
        )

    def get_back_link_params(self):
        return {
            "href": reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": self.appointment_pk},
            ),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        participant = self.appointment.participant

        context.update(
            {
                "back_link_params": self.get_back_link_params(),
                "caption": participant.full_name,
                "participant_first_name": participant.first_name,
            },
        )

        return context
