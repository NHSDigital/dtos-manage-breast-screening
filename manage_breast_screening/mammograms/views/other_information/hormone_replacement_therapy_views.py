import logging

from django.shortcuts import redirect

from manage_breast_screening.core.views.generic import (
    AddWithAuditView,
    UpdateWithAuditView,
)
from manage_breast_screening.mammograms.forms.other_information.hormone_replacement_therapy_form import (
    HormoneReplacementTherapyForm,
)

from ..mixins import MedicalInformationMixin

logger = logging.getLogger(__name__)

TEMPLATE_NAME = "mammograms/medical_information/other_information/forms/hormone_replacement_therapy.jinja"
THING_NAME = "hormone replacement therapy"


class AddHormoneReplacementTherapyView(MedicalInformationMixin, AddWithAuditView):
    form_class = HormoneReplacementTherapyForm
    template_name = TEMPLATE_NAME
    thing_name = THING_NAME

    def dispatch(self, request, *args, **kwargs):
        if hasattr(self.appointment, "hormone_replacement_therapy"):
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


class UpdateHormoneReplacementTherapyView(MedicalInformationMixin, UpdateWithAuditView):
    form_class = HormoneReplacementTherapyForm
    template_name = TEMPLATE_NAME
    thing_name = THING_NAME

    def get_object(self):
        try:
            appointment = self.appointment
            return appointment.hormone_replacement_therapy
        except AttributeError:
            logger.exception(
                "HormoneReplacementTherapy does not exist for appointment pk=%s",
                appointment.pk,
            )
            return None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["participant"] = self.participant
        return kwargs
