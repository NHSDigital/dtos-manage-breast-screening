from django.urls import reverse

from manage_breast_screening.core.template_helpers import multiline_content, nl2br
from manage_breast_screening.participants.models.medical_history.benign_lump_history_item import (
    BenignLumpHistoryItem,
)


class BenignLumpHistoryItemPresenter:
    def __init__(self, benign_lump_history_item, counter=None):
        self._item = benign_lump_history_item
        self.counter = counter

        self.right_breast_procedures = [
            BenignLumpHistoryItem.Procedure(choice).label
            for choice in self._item.right_breast_procedures
        ]
        self.left_breast_procedures = [
            BenignLumpHistoryItem.Procedure(choice).label
            for choice in self._item.left_breast_procedures
        ]

        self.procedure_year = str(self._item.procedure_year)
        self.procedure_location = self._item.get_procedure_location_display()
        self.procedure_location_details = self._item.procedure_location_details
        self.additional_details = nl2br(self._item.additional_details)

    @property
    def summary_list_params(self):
        return {
            "rows": [
                {
                    "key": {"text": "Procedures"},
                    "value": {
                        "html": multiline_content(
                            [
                                f"Right breast: {', '.join(self.right_breast_procedures)}",
                                f"Left breast: {', '.join(self.left_breast_procedures)}",
                            ]
                        )
                    },
                },
                {
                    "key": {"text": "Procedure year"},
                    "value": {"html": self.procedure_year},
                },
                {
                    "key": {"text": "Procedure location"},
                    "value": {
                        "html": f"{self.procedure_location}: {self.procedure_location_details}"
                    },
                },
                {
                    "key": {"text": "Additional details"},
                    "value": {"html": self.additional_details},
                },
            ]
        }

    @property
    def change_link(self):
        return {
            "href": reverse(
                "mammograms:change_benign_lump_history_item",
                kwargs={
                    "pk": self._item.appointment_id,
                    "history_item_pk": self._item.id,
                },
            ),
            "text": "Change",
            "visually_hidden_text": (
                f" benign lump item {self.counter}"
                if self.counter
                else " benign lump item"
            ),
        }
