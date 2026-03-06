import logging

from django.urls import reverse

from manage_breast_screening.core.views.generic import (
    AddWithAuditView,
    DeleteWithAuditView,
    UpdateWithAuditView,
)
from manage_breast_screening.mammograms.forms.medical_history.benign_lump_history_item_form import (
    BenignLumpHistoryItemForm,
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

    def confirm_delete_link_text(self, thing_name):
        return "Delete this item"

    def get_object(self):
        try:
            return self.appointment.benign_lump_history_items.get(
                pk=self.kwargs["history_item_pk"]
            )
        except AttributeError:
            logger.exception(
                "BenignLumpHistoryItem does not exist for kwargs=%s", self.kwargs
            )
            return None

    def get_delete_url(self):
        return reverse(
            "mammograms:delete_benign_lump_history_item",
            kwargs={
                "pk": self.kwargs["pk"],
                "history_item_pk": self.kwargs["history_item_pk"],
            },
        )


class DeleteBenignLumpHistoryItemView(DeleteWithAuditView):
    thing_name = "item"

    def get_success_message_content(self, object):
        return "Deleted benign lump"

    def get_object(self):
        provider = self.request.user.current_provider
        appointment = provider.appointments.get(pk=self.kwargs["pk"])
        return appointment.benign_lump_history_items.get(
            pk=self.kwargs["history_item_pk"]
        )

    def get_success_url(self) -> str:
        return reverse(
            "mammograms:record_medical_information",
            kwargs={"pk": self.kwargs["pk"]},
        )
