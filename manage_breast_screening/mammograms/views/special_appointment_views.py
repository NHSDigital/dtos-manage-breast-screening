from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import FormView

from manage_breast_screening.core.services.auditor import Auditor

from ..forms import ProvideSpecialAppointmentDetailsForm
from .mixins import AppointmentMixin


class ProvideSpecialAppointmentDetails(AppointmentMixin, FormView):
    """
    The first form you see when editing/adding special appointment details.
    The data for this is currently stored on a JSONField on the participant model.
    """

    form_class = ProvideSpecialAppointmentDetailsForm
    template_name = (
        "mammograms/special_appointments/provide_special_appointment_details.jinja"
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        context.update(
            {
                "back_link_params": {
                    "href": reverse(
                        "mammograms:show_appointment",
                        kwargs={"pk": self.appointment_pk},
                    ),
                    "text": "Back to appointment",
                },
                "caption": self.participant.full_name,
                "page_title": "Provide special appointment details",
                "heading": "Provide special appointment details",
            },
        )

        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["participant"] = self.participant
        return kwargs

    def form_valid(self, form):
        extra_needs = form.to_json()
        self.participant.extra_needs = extra_needs
        self.participant.save()
        Auditor.from_request(self.request).audit_update(self.participant)

        return redirect("mammograms:show_appointment", pk=self.appointment_pk)
