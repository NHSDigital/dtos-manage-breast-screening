import logging

from django.urls import reverse

from manage_breast_screening.core.views.generic import (
    AddWithAuditView,
    DeleteWithAuditView,
    UpdateWithAuditView,
)
from manage_breast_screening.participants.models.medical_history.implanted_medical_device_history_item import (
    ImplantedMedicalDeviceHistoryItem,
)

from ...forms.medical_history.implanted_medical_device_history_item_form import (
    ImplantedMedicalDeviceHistoryItemForm,
)
from ..mixins import MedicalInformationMixin

logger = logging.getLogger(__name__)


class AddImplantedMedicalDeviceHistoryView(MedicalInformationMixin, AddWithAuditView):
    form_class = ImplantedMedicalDeviceHistoryItemForm
    template_name = "mammograms/medical_information/medical_history/forms/implanted_medical_device_history.jinja"
    thing_name = "implanted medical device"

    def add_title(self, thing_name):
        return f"Add details of {thing_name}"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["participant"] = self.participant
        return kwargs

    def get_create_kwargs(self):
        return {"appointment": self.appointment}


class UpdateImplantedMedicalDeviceHistoryView(
    MedicalInformationMixin, UpdateWithAuditView
):
    form_class = ImplantedMedicalDeviceHistoryItemForm
    template_name = "mammograms/medical_information/medical_history/forms/implanted_medical_device_history.jinja"
    thing_name = "implanted medical device"

    def update_title(self, thing_name):
        return f"Edit details of {thing_name}"

    def confirm_delete_link_text(self, thing_name):
        return "Delete this item"

    def get_object(self):
        try:
            return ImplantedMedicalDeviceHistoryItem.objects.get(
                pk=self.kwargs["history_item_pk"],
                appointment_id=self.kwargs["pk"],
            )
        except ImplantedMedicalDeviceHistoryItem.DoesNotExist:
            logger.exception("History item does not exist for kwargs=%s", self.kwargs)
            return None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["participant"] = self.participant
        return kwargs

    def get_delete_url(self):
        return reverse(
            "mammograms:delete_implanted_medical_device_history_item",
            kwargs={
                "pk": self.kwargs["pk"],
                "history_item_pk": self.kwargs["history_item_pk"],
            },
        )


class DeleteImplantedMedicalDeviceHistoryView(DeleteWithAuditView):
    thing_name = "item"

    def get_success_message_content(self, object):
        return "Deleted implanted medical device"

    def get_object(self):
        provider = self.request.user.current_provider
        appointment = provider.appointments.get(pk=self.kwargs["pk"])
        return appointment.implanted_medical_device_history_items.get(
            pk=self.kwargs["history_item_pk"]
        )

    def get_success_url(self) -> str:
        return reverse(
            "mammograms:record_medical_information",
            kwargs={"pk": self.kwargs["pk"]},
        )
