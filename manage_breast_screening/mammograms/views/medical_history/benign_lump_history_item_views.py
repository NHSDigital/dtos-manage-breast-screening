import logging

from manage_breast_screening.core.utils.string_formatting import sentence_case
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

    def added_message(self, thing_name):
        return f"{sentence_case(thing_name)} added"

    def get_create_kwargs(self):
        return {"appointment": self.appointment}


class UpdateBenignLumpHistoryItemView(MedicalInformationMixin, UpdateWithAuditView):
    form_class = BenignLumpHistoryItemForm
    template_name = "mammograms/medical_information/medical_history/forms/benign_lump_history_item_form.jinja"
    thing_name = "benign lumps"

    def update_title(self, thing_name):
        return f"Edit details of {thing_name}"

    def updated_message(self, thing_name):
        return f"{sentence_case(thing_name)} updated"

    def get_object(self):
        try:
            return BenignLumpHistoryItem.objects.get(
                pk=self.kwargs["history_item_pk"],
                appointment_id=self.kwargs["pk"],
            )
        except BenignLumpHistoryItem.DoesNotExist:
            logger.exception("History item does not exist for kwargs=%s", self.kwargs)
            return None
