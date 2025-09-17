from functools import cached_property

from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import FormView

from manage_breast_screening.core.services.auditor import Auditor

from ..forms import MarkReasonsTemporaryForm, ProvideSpecialAppointmentDetailsForm
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

        if (
            form.cleaned_data["any_temporary"]
            == ProvideSpecialAppointmentDetailsForm.TemporaryChoices.YES
            and len(extra_needs.keys()) > 1
        ):
            return redirect("mammograms:mark_reasons_temporary", pk=self.appointment_pk)
        else:
            return redirect("mammograms:start_screening", pk=self.appointment_pk)


class MarkReasonsTemporary(AppointmentMixin, FormView):
    """
    The second form you see when editing/adding special appointment details,
    if you select "yes" for "any of these reasons are temporary" on the first form.
    The data for this is currently stored on a JSONField on the participant model.
    """

    form_class = MarkReasonsTemporaryForm
    template_name = "mammograms/special_appointments/mark_reasons_temporary.jinja"

    @cached_property
    def participant(self):
        return self.appointment.participant

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        context.update(
            {
                "back_link_params": {
                    "href": reverse(
                        "mammograms:provide_special_appointment_details",
                        kwargs={"pk": self.appointment_pk},
                    ),
                    "text": "Back",
                },
                "caption": self.participant.full_name,
                "heading": "Which of these reasons are temporary?",
            },
        )

        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["saved_data"] = self.participant.extra_needs
        return kwargs

    def form_valid(self, form):
        self.participant.extra_needs = form.to_json()
        self.participant.save()
        Auditor.from_request(self.request).audit_update(self.participant)

        return redirect("mammograms:start_screening", pk=self.appointment_pk)
