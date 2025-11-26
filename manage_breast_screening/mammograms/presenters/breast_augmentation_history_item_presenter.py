from django.urls import reverse

from manage_breast_screening.core.template_helpers import multiline_content, nl2br
from manage_breast_screening.participants.models.breast_augmentation_history_item import (
    BreastAugmentationHistoryItem,
)


class BreastAugmentationHistoryItemPresenter:
    def __init__(self, breast_augmentation_history_item, counter=None):
        self._item = breast_augmentation_history_item
        self.counter = counter

        self.right_breast_procedures = self._format_multiple_choices(
            self._item.right_breast_procedures, BreastAugmentationHistoryItem.Procedure
        )
        self.left_breast_procedures = self._format_multiple_choices(
            self._item.left_breast_procedures, BreastAugmentationHistoryItem.Procedure
        )
        self.procedure_year = str(self._item.procedure_year)
        self.implants_have_been_removed = (
            "Yes" if self._item.implants_have_been_removed else "No"
        )
        if self._item.implants_have_been_removed and self._item.removal_year:
            self.implants_have_been_removed += f" ({self._item.removal_year})"

        self.additional_details = nl2br(self._item.additional_details)

    @property
    def summary_list_params(self):
        # This is a placeholder until we have a properly formatted table.

        procedures = [
            f"Right breast: {self.right_breast_procedures}",
            f"Left breast: {self.left_breast_procedures}",
        ]

        return {
            "rows": [
                {
                    "key": {"text": "Procedures"},
                    "value": {"html": multiline_content(procedures)},
                },
                {
                    "key": {"text": "Procedure year"},
                    "value": {"html": self.procedure_year},
                },
                {
                    "key": {"text": "Implants have been removed"},
                    "value": {
                        "html": self.implants_have_been_removed,
                    },
                },
                {
                    "key": {"text": "Additional details"},
                    "value": {"html": self.additional_details},
                },
            ],
        }

    def _format_multiple_choices(self, choices, ChoiceClass):
        return ", ".join(ChoiceClass(choice).label for choice in choices)

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
