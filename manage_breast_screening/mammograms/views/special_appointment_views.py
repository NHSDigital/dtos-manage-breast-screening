from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import FormView

from manage_breast_screening.core.services.auditor import Auditor
from manage_breast_screening.core.utils.relative_redirects import (
    extract_relative_redirect_url,
)

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

    def get_return_url(self):
        return extract_relative_redirect_url(
            self.request,
            default=reverse(
                "mammograms:show_appointment",
                kwargs={"pk": self.appointment_pk},
            ),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        context.update(
            {
                "back_link_params": {
                    "href": self.get_return_url(),
                },
                "caption": self.participant.full_name,
                "page_title": "Provide special appointment details",
                "heading": "Provide special appointment details",
                "return_url": self.get_return_url(),
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

        return redirect(self.get_return_url())
