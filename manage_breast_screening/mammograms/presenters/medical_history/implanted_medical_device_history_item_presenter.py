from django.urls import reverse

from manage_breast_screening.core.template_helpers import (
    nl2br,
)


class ImplantedMedicalDeviceHistoryItemPresenter:
    def __init__(self, implanted_medical_device_history_item, counter=None):
        self._item = implanted_medical_device_history_item

        # If there are more than one of these items, we add a counter to the
        # visually hidden text
        self.counter = counter

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

    @property
    def change_link(self):
        return {
            "href": reverse(
                "mammograms:change_implanted_medical_device_history_item",
                kwargs={
                    "pk": self._item.appointment_id,
                    "history_item_pk": self._item.pk,
                },
            ),
            "text": "Change",
            "visually_hidden_text": (
                f" item {self.counter}"
                if self.counter
                else " implanted medical device item"
            ),
        }
