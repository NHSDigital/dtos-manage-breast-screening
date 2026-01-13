from django.urls import reverse

from manage_breast_screening.core.template_helpers import nl2br
from manage_breast_screening.core.utils.date_formatting import format_year_with_relative
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

        self.procedure_year = format_year_with_relative(self._item.procedure_year)
        self.procedure_location = self._item.get_procedure_location_display()
        self.procedure_location_details = self._item.procedure_location_details
        self.additional_details = nl2br(self._item.additional_details)

    @property
    def treatment_location(self):
        return {
            "type": self._item.get_procedure_location_display(),
            "details": self._item.procedure_location_details,
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
