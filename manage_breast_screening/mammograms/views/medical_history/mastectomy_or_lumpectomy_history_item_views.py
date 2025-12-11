import logging

from manage_breast_screening.core.views.generic import (
    AddWithAuditView,
    UpdateWithAuditView,
)
from manage_breast_screening.mammograms.presenters.medical_information_presenter import (
    MedicalInformationPresenter,
)
from manage_breast_screening.participants.models.medical_history.mastectomy_or_lumpectomy_history_item import (
    MastectomyOrLumpectomyHistoryItem,
)

from ...forms.medical_history.mastectomy_or_lumpectomy_history_item_form import (
    MastectomyOrLumpectomyHistoryItemForm,
)
from ..mixins import MedicalInformationMixin

logger = logging.getLogger(__name__)


class AddMastectomyOrLumpectomyHistoryView(MedicalInformationMixin, AddWithAuditView):
    form_class = MastectomyOrLumpectomyHistoryItemForm
    template_name = "mammograms/medical_information/medical_history/forms/mastectomy_or_lumpectomy_history.jinja"
    thing_name = "mastectomy or lumpectomy"

    def add_title(self, thing_name):
        return f"Add details of {thing_name}"

    def added_message(self, thing_name):
        return f"Details of {thing_name} added"

    def get_create_kwargs(self):
        return {"appointment": self.appointment}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"presenter": MedicalInformationPresenter(self.appointment)})
        return context


class UpdateMastectomyOrLumpectomyHistoryView(
    MedicalInformationMixin, UpdateWithAuditView
):
    form_class = MastectomyOrLumpectomyHistoryItemForm
    template_name = "mammograms/medical_information/medical_history/forms/mastectomy_or_lumpectomy_history.jinja"
    thing_name = "mastectomy or lumpectomy"

    def update_title(self, thing_name):
        return f"Edit details of {thing_name}"

    def updated_message(self, thing_name):
        return f"Details of {thing_name} updated"

    def get_object(self):
        try:
            return MastectomyOrLumpectomyHistoryItem.objects.get(
                pk=self.kwargs["history_item_pk"],
                appointment_id=self.kwargs["pk"],
            )
        except MastectomyOrLumpectomyHistoryItem.DoesNotExist:
            logger.exception("History item does not exist for kwargs=%s", self.kwargs)
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        context.update({"presenter": MedicalInformationPresenter(self.appointment)})

        return context
