import logging

from django.urls import reverse

from manage_breast_screening.core.utils.string_formatting import sentence_case
from manage_breast_screening.core.views.generic import (
    AddWithAuditView,
    DeleteWithAuditView,
    UpdateWithAuditView,
)
from manage_breast_screening.mammograms.forms.medical_history.breast_cancer_history_item_form import (
    BreastCancerHistoryItemForm,
)
from manage_breast_screening.participants.models.medical_history.breast_cancer_history_item import (
    BreastCancerHistoryItem,
)

from ..mixins import MedicalInformationMixin

logger = logging.getLogger(__name__)


class AddBreastCancerHistoryView(MedicalInformationMixin, AddWithAuditView):
    form_class = BreastCancerHistoryItemForm
    template_name = "mammograms/medical_information/medical_history/forms/breast_cancer_history_item_form.jinja"
    thing_name = "breast cancer"

    def add_title(self, thing_name):
        return f"Add details of {thing_name}"

    def added_message(self, thing_name):
        return f"{sentence_case(thing_name)} history added"

    def get_create_kwargs(self):
        return {"appointment": self.appointment}


class UpdateBreastCancerHistoryView(MedicalInformationMixin, UpdateWithAuditView):
    form_class = BreastCancerHistoryItemForm
    template_name = "mammograms/medical_information/medical_history/forms/breast_cancer_history_item_form.jinja"
    thing_name = "breast cancer"

    def update_title(self, thing_name):
        return f"Edit details of {thing_name}"

    def updated_message(self, thing_name):
        return f"{sentence_case(thing_name)} history updated"

    def confirm_delete_link_text(self, thing_name):
        return "Delete this item"

    def get_object(self):
        try:
            return self.appointment.breast_cancer_history_items.get(
                pk=self.kwargs["history_item_pk"],
                appointment_id=self.kwargs["pk"],
            )
        except BreastCancerHistoryItem.DoesNotExist:
            logger.exception("History item does not exist for kwargs=%s", self.kwargs)
            return None

    def get_delete_url(self):
        return reverse(
            "mammograms:delete_breast_cancer_history_item",
            kwargs={
                "pk": self.kwargs["pk"],
                "history_item_pk": self.kwargs["history_item_pk"],
            },
        )


class DeleteBreastCancerHistoryView(DeleteWithAuditView):
    thing_name = "item"

    def get_success_message_content(self, object):
        return "Deleted breast cancer"

    def get_object(self):
        provider = self.request.user.current_provider
        appointment = provider.appointments.get(pk=self.kwargs["pk"])
        return appointment.breast_cancer_history_items.get(
            pk=self.kwargs["history_item_pk"]
        )

    def get_success_url(self) -> str:
        return reverse(
            "mammograms:record_medical_information",
            kwargs={"pk": self.kwargs["pk"]},
        )
