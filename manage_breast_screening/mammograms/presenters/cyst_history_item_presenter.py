from manage_breast_screening.core.template_helpers import nl2br


class CystHistoryItemPresenter:
    def __init__(self, breast_cancer_history_item):
        self._item = breast_cancer_history_item

        self.treatment = self._item.get_treatment_display()
        self.additional_details = nl2br(self._item.additional_details)

    @property
    def summary_list_params(self):
        # This is a placeholder until we have a properly formatted table.
        return {
            "rows": [
                {
                    "key": {"text": "Treatment"},
                    "value": {"html": self.treatment},
                },
                {
                    "key": {"text": "Additional details"},
                    "value": {"html": self.additional_details},
                },
            ],
        }
