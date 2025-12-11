import logging

from django.urls import reverse

from manage_breast_screening.core.views.generic import (
    AddWithAuditView,
    DeleteWithAuditView,
    UpdateWithAuditView,
)
from manage_breast_screening.participants.models.medical_history.other_procedure_history_item import (
    OtherProcedureHistoryItem,
)

from ...forms.medical_history.other_procedure_history_item_form import (
    OtherProcedureHistoryItemForm,
)
from ..mixins import MedicalInformationMixin

logger = logging.getLogger(__name__)


class AddOtherProcedureHistoryView(MedicalInformationMixin, AddWithAuditView):
    form_class = OtherProcedureHistoryItemForm
    template_name = "mammograms/medical_information/medical_history/forms/other_procedure_history.jinja"
    thing_name = "other procedures"

    def add_title(self, thing_name):
        return f"Add details of {thing_name}"

    def added_message(self, thing_name):
        return "Details of other procedure added"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["participant"] = self.participant
        return kwargs

    def get_create_kwargs(self):
        return {"appointment": self.appointment}


class UpdateOtherProcedureHistoryView(MedicalInformationMixin, UpdateWithAuditView):
    form_class = OtherProcedureHistoryItemForm
    template_name = "mammograms/medical_information/medical_history/forms/other_procedure_history.jinja"
    thing_name = "other procedures"

    def update_title(self, thing_name):
        return f"Edit details of {thing_name}"

    def updated_message(self, thing_name):
        return "Details of other procedure updated"

    def confirm_delete_link_text(self, thing_name):
        return "Delete this item"

    def get_object(self):
        try:
            return OtherProcedureHistoryItem.objects.get(
                pk=self.kwargs["history_item_pk"],
                appointment_id=self.kwargs["pk"],
            )
        except OtherProcedureHistoryItem.DoesNotExist:
            logger.exception("History item does not exist for kwargs=%s", self.kwargs)
            return None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["participant"] = self.participant
        return kwargs

    def get_delete_url(self):
        return reverse(
            "mammograms:delete_other_procedure_history_item",
            kwargs={
                "pk": self.kwargs["pk"],
                "history_item_pk": self.kwargs["history_item_pk"],
            },
        )


class DeleteOtherProcedureHistoryView(DeleteWithAuditView):
    def get_thing_name(self, object):
        return "item"

    def get_success_message_content(self, object):
        return "Deleted other procedure"

    def get_object(self):
        provider = self.request.user.current_provider
        appointment = provider.appointments.get(pk=self.kwargs["pk"])
        return appointment.other_procedure_history_items.get(
            pk=self.kwargs["history_item_pk"]
        )

    def get_success_url(self) -> str:
        return reverse(
            "mammograms:record_medical_information",
            kwargs={"pk": self.kwargs["pk"]},
        )
