import logging

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

    def add_title(self, thing_name):
        return f"Add details of {thing_name}"

    def added_message(self, thing_name):
        return f"Details of {thing_name} added"

    def get_create_kwargs(self):
        return {"appointment": self.appointment}


class UpdateBreastAugmentationHistoryView(MedicalInformationMixin, UpdateWithAuditView):
    form_class = BreastAugmentationHistoryItemForm
    template_name = "mammograms/medical_information/medical_history/forms/breast_augmentation_history.jinja"
    thing_name = "breast implants or augmentation"

    def update_title(self, thing_name):
        return f"Edit details of {thing_name}"

    def updated_message(self, thing_name):
        return f"Details of {thing_name} updated"

    def get_object(self):
        try:
            return BreastAugmentationHistoryItem.objects.get(
                pk=self.kwargs["history_item_pk"],
                appointment_id=self.kwargs["pk"],
            )
        except BreastAugmentationHistoryItem.DoesNotExist:
            logger.exception("History item does not exist for kwargs=%s", self.kwargs)
            return None
