from manage_breast_screening.core.template_helpers import multiline_content, nl2br
from manage_breast_screening.participants.models.mastectomy_or_lumpectomy_history_item import (
    MastectomyOrLumpectomyHistoryItem,
)


class MastectomyOrLumpectomyHistoryItemPresenter:
    def __init__(self, mastectomy_or_lumpectomy_history_item):
        self._item = mastectomy_or_lumpectomy_history_item

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
                                f"Right breast: {self.right_breast_procedure}",
                                f"Left breast: {self.left_breast_procedure}",
                            ]
                        )
                    },
                },
                {
                    "key": {"text": "Other surgery"},
                    "value": {
                        "html": multiline_content(
                            [
                                f"Right breast: {self.right_breast_other_surgery}",
                                f"Left breast: {self.left_breast_other_surgery}",
                            ]
                        )
                    },
                },
                {
                    "key": {"text": "Year of surgery"},
                    "value": {"html": self.year_of_surgery},
                },
                {
                    "key": {"text": "Surgery reason"},
                    "value": {"html": self.surgery_reason},
                },
                {
                    "key": {"text": "Additional details"},
                    "value": {"html": self.additional_details},
                },
            ],
        }

    def _format_multiple_choices(self, choices, ChoiceClass):
        return ", ".join(ChoiceClass(choice).label for choice in choices)
