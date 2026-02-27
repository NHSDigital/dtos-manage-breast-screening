import logging

from django.shortcuts import redirect

from manage_breast_screening.core.views.generic import (
    AddWithAuditView,
    UpdateWithAuditView,
)
from manage_breast_screening.mammograms.forms.other_information.other_medical_information_form import (
    OtherMedicalInformationForm,
)

from ..mixins import MedicalInformationMixin

logger = logging.getLogger(__name__)

TEMPLATE_NAME = "mammograms/medical_information/other_information/forms/other_medical_information.jinja"
THING_NAME = "other medical information"


class AddOtherMedicalInformationView(MedicalInformationMixin, AddWithAuditView):
    form_class = OtherMedicalInformationForm
    template_name = TEMPLATE_NAME
    thing_name = THING_NAME

    def dispatch(self, request, *args, **kwargs):
        if hasattr(self.appointment, "other_medical_information"):
            return redirect(
                "mammograms:record_medical_information",
                pk=self.appointment.pk,
            )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["participant"] = self.participant
        return kwargs

    def get_create_kwargs(self):
        return {"appointment": self.appointment}


class UpdateOtherMedicalInformationView(MedicalInformationMixin, UpdateWithAuditView):
    form_class = OtherMedicalInformationForm
    template_name = TEMPLATE_NAME
    thing_name = THING_NAME

    def get_object(self):
        try:
            appointment = self.appointment
            return appointment.other_medical_information
        except AttributeError:
            logger.exception(
                "OtherMedicalInformation does not exist for appointment pk=%s",
                appointment.pk,
            )
            return None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["participant"] = self.participant
        return kwargs
