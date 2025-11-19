from manage_breast_screening.core.template_helpers import multiline_content, nl2br
from manage_breast_screening.participants.models.breast_cancer_history_item import (
    BreastCancerHistoryItem,
)


class BreastCancerHistoryItemPresenter:
    def __init__(self, breast_cancer_history_item):
        self._item = breast_cancer_history_item

        self.cancer_location = self._item.get_diagnosis_location_display()
        self.right_breast_procedures = self._item.get_right_breast_procedure_display()
        self.left_breast_procedures = self._item.get_left_breast_procedure_display()

        self.right_breast_other_surgery = self._format_multiple_choices(
            self._item.right_breast_other_surgery, BreastCancerHistoryItem.Surgery
        )
        self.left_breast_other_surgery = self._format_multiple_choices(
            self._item.left_breast_other_surgery, BreastCancerHistoryItem.Surgery
        )
        self.right_breast_treatment = self._format_multiple_choices(
            self._item.right_breast_treatment, BreastCancerHistoryItem.Treatment
        )
        self.left_breast_treatment = self._format_multiple_choices(
            self._item.left_breast_treatment, BreastCancerHistoryItem.Treatment
        )
        self.systemic_treatments = self._format_multiple_choices(
            self._item.systemic_treatments,
            BreastCancerHistoryItem.SystemicTreatment,
        )
        self.additional_details = nl2br(self._item.additional_details)

    @property
    def summary_list_params(self):
        # This is a placeholder until we have a properly formatted table.
        return {
            "rows": [
                {
                    "key": {"text": "Cancer location"},
                    "value": {"html": self.cancer_location},
                },
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
                    "key": {"text": "Treatment"},
                    "value": {
                        "html": multiline_content(
                            [
                                f"Right breast: {self.right_breast_treatment}",
                                f"Left breast: {self.left_breast_treatment}",
                                f"Systemic treatements: {self.systemic_treatments}",
                            ]
                        )
                    },
                },
                {
                    "key": {"text": "Treatment location"},
                    "value": {
                        "html": self._item.get_intervention_location_display()
                        + ": "
                        + self._item.intervention_location_details
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
