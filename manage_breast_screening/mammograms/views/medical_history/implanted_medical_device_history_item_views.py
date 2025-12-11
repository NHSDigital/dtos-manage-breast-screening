import logging

from manage_breast_screening.core.utils.string_formatting import sentence_case
from manage_breast_screening.core.views.generic import (
    AddWithAuditView,
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

    def added_message(self, thing_name):
        return f"{sentence_case(thing_name)} added"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        context.update({"page_title": "Details of the implanted medical device"})

        return context

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

    def updated_message(self, thing_name):
        return f"Details of {thing_name} updated"

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        context.update({"page_title": "Details of the implanted medical device"})

        return context
