import logging

from manage_breast_screening.core.views.generic import (
    AddWithAuditView,
    UpdateWithAuditView,
)
from manage_breast_screening.mammograms.forms.medical_history.benign_lump_history_item_form import (
    BenignLumpHistoryItemForm,
)
from manage_breast_screening.participants.models.medical_history.benign_lump_history_item import (
    BenignLumpHistoryItem,
)

from ..mixins import MedicalInformationMixin

logger = logging.getLogger(__name__)


class AddBenignLumpHistoryItemView(MedicalInformationMixin, AddWithAuditView):
    form_class = BenignLumpHistoryItemForm
    template_name = "mammograms/medical_information/medical_history/forms/benign_lump_history_item_form.jinja"
    thing_name = "benign lumps"

    def add_title(self, thing_name):
        return f"Add details of {thing_name}"

    def get_create_kwargs(self):
        return {"appointment": self.appointment}


class UpdateBenignLumpHistoryItemView(MedicalInformationMixin, UpdateWithAuditView):
    form_class = BenignLumpHistoryItemForm
    template_name = "mammograms/medical_information/medical_history/forms/benign_lump_history_item_form.jinja"
    thing_name = "benign lumps"

    def update_title(self, thing_name):
        return f"Edit details of {thing_name}"

    def get_object(self):
        try:
            return BenignLumpHistoryItem.objects.get(
                pk=self.kwargs["history_item_pk"],
                appointment_id=self.kwargs["pk"],
            )
        except BenignLumpHistoryItem.DoesNotExist:
            logger.exception("History item does not exist for kwargs=%s", self.kwargs)
            return None
