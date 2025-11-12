from manage_breast_screening.core.template_helpers import nl2br


class OtherProcedureHistoryItemPresenter:
    def __init__(self, implanted_medical_device_history_item):
        self._item = implanted_medical_device_history_item

        self.procedure = self._item.get_procedure_display()
        self.procedure_details = self._item.procedure_details or "N/A"
        self.procedure_year = str(self._item.procedure_year)
        self.additional_details = nl2br(self._item.additional_details)

    @property
    def summary_list_params(self):
        # This is a placeholder until we have a properly formatted table.
        return {
            "rows": [
                {
                    "key": {"text": "Procedure"},
                    "value": {"html": self.procedure},
                },
                {
                    "key": {"text": "Procedure details"},
                    "value": {"html": self.procedure_details},
                },
                {
                    "key": {"text": "Procedure year"},
                    "value": {"html": self.procedure_year},
                },
                {
                    "key": {"text": "Additional details"},
                    "value": {"html": self.additional_details},
                },
            ],
        }
