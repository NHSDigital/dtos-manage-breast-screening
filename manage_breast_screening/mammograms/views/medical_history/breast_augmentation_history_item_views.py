import logging

from django.shortcuts import redirect
from django.urls import reverse

from manage_breast_screening.core.views.generic import (
    AddWithAuditView,
    DeleteWithAuditView,
    UpdateWithAuditView,
)

from ...forms.medical_history.breast_augmentation_history_item_form import (
    BreastAugmentationHistoryItemForm,
)
from ..mixins import MedicalInformationMixin

logger = logging.getLogger(__name__)


class AddBreastAugmentationHistoryView(MedicalInformationMixin, AddWithAuditView):
    form_class = BreastAugmentationHistoryItemForm
    template_name = "mammograms/medical_information/medical_history/forms/breast_augmentation_history.jinja"
    thing_name = "breast implants or augmentation"

    def dispatch(self, request, *args, **kwargs):
        if self.appointment.breast_augmentation_history_items.exists():
            return redirect(
                "mammograms:record_medical_information",
                pk=self.appointment.pk,
            )
        return super().dispatch(request, *args, **kwargs)

    def add_title(self, thing_name):
        return f"Add details of {thing_name}"

    def get_create_kwargs(self):
        return {"appointment": self.appointment}


class UpdateBreastAugmentationHistoryView(MedicalInformationMixin, UpdateWithAuditView):
    form_class = BreastAugmentationHistoryItemForm
    template_name = "mammograms/medical_information/medical_history/forms/breast_augmentation_history.jinja"
    thing_name = "breast implants or augmentation"

    def update_title(self, thing_name):
        return f"Edit details of {thing_name}"

    def confirm_delete_link_text(self, thing_name):
        return "Delete this item"

    def get_object(self):
        try:
            return self.appointment.breast_augmentation_history_items.get(
                pk=self.kwargs["history_item_pk"]
            )
        except AttributeError:
            logger.exception(
                "BreastAugmentationHistoryItem does not exist for kwargs=%s",
                self.kwargs,
            )
            return None

    def get_delete_url(self):
        return reverse(
            "mammograms:delete_breast_augmentation_history_item",
            kwargs={
                "pk": self.kwargs["pk"],
                "history_item_pk": self.kwargs["history_item_pk"],
            },
        )


class DeleteBreastAugmentationHistoryView(DeleteWithAuditView):
    thing_name = "item"

    def get_success_message_content(self, object):
        return "Deleted breast implants or augmentation"

    def get_object(self):
        provider = self.request.user.current_provider
        appointment = provider.appointments.get(pk=self.kwargs["pk"])
        return appointment.breast_augmentation_history_items.get(
            pk=self.kwargs["history_item_pk"]
        )

    def get_success_url(self) -> str:
        return reverse(
            "mammograms:record_medical_information",
            kwargs={"pk": self.kwargs["pk"]},
        )
