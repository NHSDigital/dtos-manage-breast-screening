import logging

from django.shortcuts import redirect
from django.urls import reverse

from manage_breast_screening.core.views.generic import (
    AddWithAuditView,
    DeleteWithAuditView,
    UpdateWithAuditView,
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

    def dispatch(self, request, *args, **kwargs):
        if self.appointment.cyst_history_items.exists():
            return redirect(
                "mammograms:record_medical_information",
                pk=self.appointment.pk,
            )
        return super().dispatch(request, *args, **kwargs)

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

    def confirm_delete_link_text(self, thing_name):
        return "Delete this item"

    def get_object(self):
        try:
            return self.appointment.cyst_history_items.get(
                pk=self.kwargs["history_item_pk"]
            )
        except AttributeError:
            logger.exception(
                "CystHistoryItem does not exist for kwargs=%s", self.kwargs
            )
            return None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["participant"] = self.participant
        return kwargs

    def get_delete_url(self):
        return reverse(
            "mammograms:delete_cyst_history_item",
            kwargs={
                "pk": self.kwargs["pk"],
                "history_item_pk": self.kwargs["history_item_pk"],
            },
        )


class DeleteCystHistoryView(DeleteWithAuditView):
    thing_name = "item"

    def get_success_message_content(self, object):
        return "Deleted cysts"

    def get_object(self):
        provider = self.request.user.current_provider
        appointment = provider.appointments.get(pk=self.kwargs["pk"])
        return appointment.cyst_history_items.get(pk=self.kwargs["history_item_pk"])

    def get_success_url(self) -> str:
        return reverse(
            "mammograms:record_medical_information",
            kwargs={"pk": self.kwargs["pk"]},
        )
