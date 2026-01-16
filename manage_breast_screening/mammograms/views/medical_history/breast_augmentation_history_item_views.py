import logging

from django.shortcuts import redirect

from manage_breast_screening.core.views.generic import (
    AddWithAuditView,
    UpdateWithAuditView,
)
from manage_breast_screening.participants.models.medical_history.breast_augmentation_history_item import (
    BreastAugmentationHistoryItem,
)

from ...forms.medical_history.breast_augmentation_history_item_form import (
    BreastAugmentationHistoryItemForm,
)
from ..mixins import MedicalInformationMixin

logger = logging.getLogger(__name__)


class AddBreastAugmentationHistoryView(MedicalInformationMixin, AddWithAuditView):
    form_class = BreastAugmentationHistoryItemForm
    template_name = "mammograms/medical_information/medical_history/forms/breast_augmentation_history.jinja"
    thing_name = "breast implants or augmentation"

    def dispatch(self, request, *args, **kwargs):
        if self.appointment.breast_augmentation_history_items.exists():
            return redirect(
                "mammograms:record_medical_information",
                pk=self.appointment.pk,
            )
        return super().dispatch(request, *args, **kwargs)

    def add_title(self, thing_name):
        return f"Add details of {thing_name}"

    def get_create_kwargs(self):
        return {"appointment": self.appointment}


class UpdateBreastAugmentationHistoryView(MedicalInformationMixin, UpdateWithAuditView):
    form_class = BreastAugmentationHistoryItemForm
    template_name = "mammograms/medical_information/medical_history/forms/breast_augmentation_history.jinja"
    thing_name = "breast implants or augmentation"

    def update_title(self, thing_name):
        return f"Edit details of {thing_name}"

    def get_object(self):
        try:
            return BreastAugmentationHistoryItem.objects.get(
                pk=self.kwargs["history_item_pk"],
                appointment_id=self.kwargs["pk"],
            )
        except BreastAugmentationHistoryItem.DoesNotExist:
            logger.exception("History item does not exist for kwargs=%s", self.kwargs)
            return None
