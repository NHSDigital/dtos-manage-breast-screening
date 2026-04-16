from django.urls import reverse

from manage_breast_screening.core.models import get_object_or_none
from manage_breast_screening.core.views.generic import (
    AddWithAuditView,
    DeleteWithAuditView,
    UpdateWithAuditView,
)

from ...forms.medical_history.other_procedure_history_item_form import (
    OtherProcedureHistoryItemForm,
)
from ..mixins import MedicalInformationMixin


class AddOtherProcedureHistoryView(MedicalInformationMixin, AddWithAuditView):
    form_class = OtherProcedureHistoryItemForm
    template_name = "mammograms/medical_information/medical_history/forms/other_procedure_history.jinja"
    thing_name = "other procedures"

    def add_title(self, thing_name):
        return f"Add details of {thing_name}"

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

    def confirm_delete_link_text(self, thing_name):
        return "Delete this item"

    def get_object(self):
        return get_object_or_none(
            self.appointment.other_procedure_history_items,
            pk=self.kwargs.get("history_item_pk"),
        )

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


class DeleteOtherProcedureHistoryView(MedicalInformationMixin, DeleteWithAuditView):
    def get_thing_name(self, object):
        return "item"

    def get_success_message_content(self, object):
        return "Deleted other procedure"

    def get_object(self):
        return self.appointment.other_procedure_history_items.get(
            pk=self.kwargs["history_item_pk"]
        )
