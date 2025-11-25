from manage_breast_screening.core.template_helpers import (
    nl2br,
)


class ImplantedMedicalDeviceHistoryItemPresenter:
    def __init__(self, implanted_medical_device_history_item):
        self._item = implanted_medical_device_history_item

        self.device = self._item.get_device_display()
        self.other_medical_device_details = (
            self._item.other_medical_device_details or "N/A"
        )
        self.procedure_year = str(self._item.procedure_year)
        self.device_has_been_removed = (
            "Yes" if self._item.device_has_been_removed else "No"
        )
        if self._item.device_has_been_removed and self._item.removal_year:
            self.device_has_been_removed += f" ({self._item.removal_year})"
        self.additional_details = nl2br(self._item.additional_details)

    @property
    def summary_list_params(self):
        # This is a placeholder until we have a properly formatted table.
        return {
            "rows": [
                {
                    "key": {"text": "Device"},
                    "value": {"html": self.device},
                },
                {
                    "key": {"text": "Other medical device details"},
                    "value": {"html": self.other_medical_device_details},
                },
                {
                    "key": {"text": "Procedure year"},
                    "value": {"html": self.procedure_year},
                },
                {
                    "key": {"text": "Device has been removed"},
                    "value": {
                        "html": self.device_has_been_removed,
                    },
                },
                {
                    "key": {"text": "Additional details"},
                    "value": {"html": self.additional_details},
                },
            ],
        }
