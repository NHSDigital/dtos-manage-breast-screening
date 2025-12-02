from django.urls import reverse

from manage_breast_screening.core.template_helpers import multiline_content, nl2br
from manage_breast_screening.participants.models.benign_lump_history_item import (
    BenignLumpHistoryItem,
)


class BenignLumpHistoryItemPresenter:
    def __init__(self, benign_lump_history_item):
        self._item = benign_lump_history_item
        self.right_breast_procedures = self._format_multiple_choices(
            self._item.right_breast_procedures, BenignLumpHistoryItem.Procedure
        )
        self.left_breast_procedures = self._format_multiple_choices(
            self._item.left_breast_procedures, BenignLumpHistoryItem.Procedure
        )
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
                                f"Right breast: {self.right_breast_procedures}",
                                f"Left breast: {self.left_breast_procedures}",
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
        }

    def _format_multiple_choices(self, choices, ChoiceClass):
        return ", ".join(ChoiceClass(choice).label for choice in choices)
