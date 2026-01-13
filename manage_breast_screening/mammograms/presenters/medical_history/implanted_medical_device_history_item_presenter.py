from django.urls import reverse

from manage_breast_screening.core.template_helpers import multiline_content, nl2br
from manage_breast_screening.core.utils.date_formatting import format_year_with_relative
from manage_breast_screening.participants.models.medical_history.implanted_medical_device_history_item import (
    ImplantedMedicalDeviceHistoryItem,
)


class ImplantedMedicalDeviceHistoryItemPresenter:
    def __init__(self, implanted_medical_device_history_item, counter=None):
        self._item = implanted_medical_device_history_item

        # If there are more than one of these items, we add a counter to the
        # visually hidden text
        self.counter = counter

        self.other_medical_device_details = (
            self._item.other_medical_device_details or "N/A"
        )

        self.device_has_been_removed = (
            "Yes" if self._item.device_has_been_removed else "No"
        )
        if self._item.device_has_been_removed and self._item.removal_year:
            self.device_has_been_removed += f" ({self._item.removal_year})"
        self.additional_details = nl2br(self._item.additional_details)

    @property
    def procedure_year(self):
        return format_year_with_relative(self._item.procedure_year)

    @property
    def removal_year(self):
        return format_year_with_relative(self._item.removal_year)

    @property
    def device(self):
        mapping = {
            ImplantedMedicalDeviceHistoryItem.Device.CARDIAC_DEVICE: "Cardiac device",
            ImplantedMedicalDeviceHistoryItem.Device.OTHER_MEDICAL_DEVICE: "Other medical device",
        }
        return mapping.get(self._item.device, self._item.get_device_display())

    @property
    def procedure_year_with_removal(self):
        lines = []
        if self.procedure_year:
            lines.append(f"Implanted in {self.procedure_year}")

        if self._item.removal_year:
            lines.append(f"Device removed in {self.removal_year}")
        elif self._item.device_has_been_removed:
            lines.append("Device removed")

        return multiline_content(lines)

    @property
    def type(self):
        device = self.device
        details = self._item.other_medical_device_details
        if (
            self._item.device
            == ImplantedMedicalDeviceHistoryItem.Device.OTHER_MEDICAL_DEVICE
            and details
        ):
            return f"Other medical device: {details}"
        else:
            return device

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
