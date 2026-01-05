from django.urls import reverse

from manage_breast_screening.core.template_helpers import nl2br
from manage_breast_screening.participants.models.medical_history.mastectomy_or_lumpectomy_history_item import (
    MastectomyOrLumpectomyHistoryItem,
)


class MastectomyOrLumpectomyHistoryItemPresenter:
    def __init__(self, mastectomy_or_lumpectomy_history_item, counter=None):
        self._item = mastectomy_or_lumpectomy_history_item

        # If there are more than one of these items, we add a counter to the
        # visually hidden text
        self.counter = counter

        self.right_breast_procedure = self._item.get_right_breast_procedure_display()
        self.left_breast_procedure = self._item.get_left_breast_procedure_display()

        self.right_breast_other_surgery = self._format_multiple_choices(
            self._item.right_breast_other_surgery,
            MastectomyOrLumpectomyHistoryItem.Surgery,
        )
        self.left_breast_other_surgery = self._format_multiple_choices(
            self._item.left_breast_other_surgery,
            MastectomyOrLumpectomyHistoryItem.Surgery,
        )
        self.year_of_surgery = (
            str(self._item.year_of_surgery)
            if self._item.year_of_surgery
            else "Not specified"
        )
        self.surgery_reason = self._item.get_surgery_reason_display()
        self.surgery_other_reason_details = self._item.surgery_other_reason_details
        self.additional_details = nl2br(self._item.additional_details)

    def _format_multiple_choices(self, choices, ChoiceClass):
        return [ChoiceClass(choice).label for choice in choices]

    @property
    def change_link(self):
        return {
            "href": reverse(
                "mammograms:change_mastectomy_or_lumpectomy_history_item",
                kwargs={
                    "pk": self._item.appointment_id,
                    "history_item_pk": self._item.pk,
                },
            ),
            "text": "Change",
            "visually_hidden_text": (
                f" mastectomy or lumpectomy item {self.counter}"
                if self.counter
                else " mastectomy or lumpectomy item"
            ),
        }
