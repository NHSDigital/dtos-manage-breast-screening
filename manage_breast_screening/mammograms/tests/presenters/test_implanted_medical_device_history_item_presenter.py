from manage_breast_screening.mammograms.presenters.implanted_medical_device_history_item_presenter import (
    ImplantedMedicalDeviceHistoryItemPresenter,
)
from manage_breast_screening.participants.models.implanted_medical_device_history_item import (
    ImplantedMedicalDeviceHistoryItem,
)
from manage_breast_screening.participants.tests.factories import (
    ImplantedMedicalDeviceHistoryItemFactory,
)


class TestImplantedMedicalDeviceHistoryItemPresenter:
    def test_single(self):
        item = ImplantedMedicalDeviceHistoryItemFactory.build(
            device=ImplantedMedicalDeviceHistoryItem.Device.OTHER_MEDICAL_DEVICE,
            other_medical_device_details="Test Device",
            procedure_year=2020,
            device_has_been_removed=True,
            removal_year=2022,
            additional_details="Some additional details",
        )

        presenter = ImplantedMedicalDeviceHistoryItemPresenter(item)
        assert presenter.summary_list_params == {
            "rows": [
                {
                    "key": {
                        "text": "Device",
                    },
                    "value": {
                        "html": "Other medical device (or does not know)",
                    },
                },
                {
                    "key": {
                        "text": "Other medical device details",
                    },
                    "value": {
                        "html": "Test Device",
                    },
                },
                {
                    "key": {
                        "text": "Procedure year",
                    },
                    "value": {
                        "html": "2020",
                    },
                },
                {
                    "key": {
                        "text": "Device has been removed",
                    },
                    "value": {
                        "html": "Yes (2022)",
                    },
                },
                {
                    "key": {
                        "text": "Additional details",
                    },
                    "value": {
                        "html": "Some additional details",
                    },
                },
            ],
        }
