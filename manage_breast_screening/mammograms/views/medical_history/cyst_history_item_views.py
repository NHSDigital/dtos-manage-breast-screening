import logging

from manage_breast_screening.core.views.generic import (
    AddWithAuditView,
    UpdateWithAuditView,
)
from manage_breast_screening.participants.models.medical_history.cyst_history_item import (
    CystHistoryItem,
)

from ...forms.medical_history.cyst_history_item_form import CystHistoryItemForm
from ..mixins import MedicalInformationMixin

logger = logging.getLogger(__name__)


class AddCystHistoryView(MedicalInformationMixin, AddWithAuditView):
    form_class = CystHistoryItemForm
    template_name = (
        "mammograms/medical_information/medical_history/forms/cyst_history.jinja"
    )
    thing_name = "cysts"

    def add_title(self, thing_name):
        return f"Add details of {thing_name}"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["participant"] = self.participant
        return kwargs

    def get_create_kwargs(self):
        return {"appointment": self.appointment}


class UpdateCystHistoryView(MedicalInformationMixin, UpdateWithAuditView):
    form_class = CystHistoryItemForm
    template_name = (
        "mammograms/medical_information/medical_history/forms/cyst_history.jinja"
    )
    thing_name = "cysts"

    def update_title(self, thing_name):
        return f"Edit details of {thing_name}"

    def get_object(self):
        try:
            return CystHistoryItem.objects.get(
                pk=self.kwargs["history_item_pk"],
                appointment_id=self.kwargs["pk"],
            )
        except CystHistoryItem.DoesNotExist:
            logger.exception("History item does not exist for kwargs=%s", self.kwargs)
            return None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["participant"] = self.participant
        return kwargs
