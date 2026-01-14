from django.urls import reverse

from manage_breast_screening.core.template_helpers import multiline_content, nl2br
from manage_breast_screening.core.utils.date_formatting import format_year_with_relative
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

        self.right_breast_other_surgery = [
            MastectomyOrLumpectomyHistoryItem.Surgery(choice).label
            for choice in self._item.right_breast_other_surgery
        ]
        self.left_breast_other_surgery = [
            MastectomyOrLumpectomyHistoryItem.Surgery(choice).label
            for choice in self._item.left_breast_other_surgery
        ]

        self.year_of_surgery = (
            format_year_with_relative(self._item.year_of_surgery)
            if self._item.year_of_surgery
            else "Not specified"
        )
        self.additional_details = nl2br(self._item.additional_details)

    @property
    def surgery_reason(self):
        reason = self._item.get_surgery_reason_display()
        details = self._item.surgery_other_reason_details

        if (
            self._item.surgery_reason
            == MastectomyOrLumpectomyHistoryItem.SurgeryReason.OTHER_REASON
            and details
        ):
            return multiline_content([reason, f"Details: {details}"])
        else:
            return reason

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
        }
