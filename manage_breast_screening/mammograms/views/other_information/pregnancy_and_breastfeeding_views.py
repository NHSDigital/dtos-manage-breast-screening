import logging

from django.shortcuts import redirect

from manage_breast_screening.core.views.generic import (
    AddWithAuditView,
    UpdateWithAuditView,
)
from manage_breast_screening.mammograms.forms.other_information.pregnancy_and_breastfeeding_form import (
    PregnancyAndBreastfeedingForm,
)

from ..mixins import MedicalInformationMixin

logger = logging.getLogger(__name__)

TEMPLATE_NAME = "mammograms/medical_information/other_information/forms/pregnancy_and_breastfeeding.jinja"
THING_NAME = "pregnancy and breastfeeding"
TITLE = "Pregnancy and breastfeeding"


class AddPregnancyAndBreastfeedingView(MedicalInformationMixin, AddWithAuditView):
    form_class = PregnancyAndBreastfeedingForm
    template_name = TEMPLATE_NAME
    thing_name = THING_NAME

    def add_title(self, thing_name):
        return TITLE

    def dispatch(self, request, *args, **kwargs):
        if hasattr(self.appointment, "pregnancy_and_breastfeeding"):
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


class UpdatePregnancyAndBreastfeedingView(MedicalInformationMixin, UpdateWithAuditView):
    form_class = PregnancyAndBreastfeedingForm
    template_name = TEMPLATE_NAME
    thing_name = THING_NAME

    def update_title(self, thing_name):
        return TITLE

    def get_object(self):
        try:
            appointment = self.appointment
            return appointment.pregnancy_and_breastfeeding
        except AttributeError:
            logger.exception(
                "PregnancyAndBreastfeeding does not exist for appointment pk=%s",
                appointment.pk,
            )
            return None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["participant"] = self.participant
        return kwargs
