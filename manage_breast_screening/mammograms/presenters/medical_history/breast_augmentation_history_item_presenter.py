from django.urls import reverse

from manage_breast_screening.core.template_helpers import multiline_content, nl2br
from manage_breast_screening.core.utils.date_formatting import format_year_with_relative
from manage_breast_screening.participants.models.medical_history.breast_augmentation_history_item import (
    BreastAugmentationHistoryItem,
)


class BreastAugmentationHistoryItemPresenter:
    def __init__(self, breast_augmentation_history_item, counter=None):
        self._item = breast_augmentation_history_item
        self.counter = counter

        self.right_breast_procedures = [
            self._procedure_text(choice)
            for choice in self._item.right_breast_procedures
        ]
        self.left_breast_procedures = [
            self._procedure_text(choice) for choice in self._item.left_breast_procedures
        ]

        self.implants_have_been_removed = (
            "Yes" if self._item.implants_have_been_removed else "No"
        )
        if self._item.implants_have_been_removed and self._item.removal_year:
            self.implants_have_been_removed += f" ({self._item.removal_year})"

        self.additional_details = nl2br(self._item.additional_details)

    @property
    def procedure_year(self):
        return format_year_with_relative(self._item.procedure_year)

    @property
    def removal_year(self):
        return format_year_with_relative(self._item.removal_year)

    @property
    def procedure_year_with_removal(self):
        lines = []
        if self.procedure_year:
            lines.append(f"Implanted in {self.procedure_year}")

        if self._item.removal_year:
            lines.append(f"Implants removed in {self.removal_year}")
        elif self._item.implants_have_been_removed:
            lines.append("Implants removed")

        return multiline_content(lines)

    @property
    def change_link(self):
        return {
            "href": reverse(
                "mammograms:change_breast_augmentation_history_item",
                kwargs={
                    "pk": self._item.appointment_id,
                    "history_item_pk": self._item.pk,
                },
            ),
            "text": "Change",
            "visually_hidden_text": (
                f" breast implants or augmentation item {self.counter}"
                if self.counter
                else " breast implants or augmentation item"
            ),
        }

    def _procedure_text(self, procedure):
        if procedure == BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS:
            return "Breast implants"
        else:
            return BreastAugmentationHistoryItem.Procedure(procedure).label
