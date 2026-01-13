from datetime import date

import pytest
import time_machine

from manage_breast_screening.mammograms.presenters.medical_history.implanted_medical_device_history_item_presenter import (
    ImplantedMedicalDeviceHistoryItemPresenter,
)
from manage_breast_screening.participants.models.medical_history.implanted_medical_device_history_item import (
    ImplantedMedicalDeviceHistoryItem,
)
from manage_breast_screening.participants.tests.factories import (
    ImplantedMedicalDeviceHistoryItemFactory,
)


class TestImplantedMedicalDeviceHistoryItemPresenter:
    @pytest.fixture
    def item(self):
        return ImplantedMedicalDeviceHistoryItemFactory.build(
            device=ImplantedMedicalDeviceHistoryItem.Device.OTHER_MEDICAL_DEVICE,
            other_medical_device_details="Test Device",
            procedure_year=2020,
            device_has_been_removed=True,
            removal_year=2022,
            additional_details="Some additional details",
        )

    @pytest.fixture
    @time_machine.travel(date(2025, 1, 1))
    def presenter(self, item):
        return ImplantedMedicalDeviceHistoryItemPresenter(item)

    @time_machine.travel(date(2025, 1, 1))
    def test_attributes(self, presenter):
        assert presenter.device == "Other medical device"
        assert presenter.procedure_year == "2020 (5 years ago)"
        assert presenter.removal_year == "2022 (3 years ago)"
        assert presenter.additional_details == "Some additional details"

    @pytest.mark.parametrize(
        "device, expected",
        [
            (ImplantedMedicalDeviceHistoryItem.Device.CARDIAC_DEVICE, "Cardiac device"),
            (ImplantedMedicalDeviceHistoryItem.Device.HICKMAN_LINE, "Hickman line"),
            (
                ImplantedMedicalDeviceHistoryItem.Device.OTHER_MEDICAL_DEVICE,
                "Other medical device",
            ),
        ],
    )
    @time_machine.travel(date(2025, 1, 1))
    def test_device_removes_parenthetical_text(self, device, expected):
        item = ImplantedMedicalDeviceHistoryItemFactory.build(device=device)
        presenter = ImplantedMedicalDeviceHistoryItemPresenter(item)

        assert presenter.device == expected

    @time_machine.travel(date(2025, 1, 1))
    def test_procedure_year_with_removal(self, presenter):
        assert presenter.procedure_year_with_removal == (
            "Implanted in 2020 (5 years ago)<br>Device removed in 2022 (3 years ago)"
        )

    @time_machine.travel(date(2025, 1, 1))
    def test_missing_procedure_year(self):
        presenter = ImplantedMedicalDeviceHistoryItemPresenter(
            ImplantedMedicalDeviceHistoryItemFactory.build(
                device=ImplantedMedicalDeviceHistoryItem.Device.OTHER_MEDICAL_DEVICE,
                other_medical_device_details="Test Device",
                additional_details="Some additional details",
            )
        )
        assert presenter.procedure_year_with_removal == ""

    def test_change_link(self):
        item = ImplantedMedicalDeviceHistoryItemFactory.build(
            device=ImplantedMedicalDeviceHistoryItem.Device.CARDIAC_DEVICE,
            additional_details="Some additional details",
        )

        presenter = ImplantedMedicalDeviceHistoryItemPresenter(item)
        assert presenter.change_link == {
            "href": f"/mammograms/{item.appointment_id}/record-medical-information/implanted-medical-device-history/{item.pk}/",
            "text": "Change",
            "visually_hidden_text": " implanted medical device item",
        }

    def test_change_link_with_counter(self):
        item = ImplantedMedicalDeviceHistoryItemFactory.build(
            device=ImplantedMedicalDeviceHistoryItem.Device.CARDIAC_DEVICE,
            additional_details="Some additional details",
        )

        presenter = ImplantedMedicalDeviceHistoryItemPresenter(item, counter=2)
        assert presenter.change_link == {
            "href": f"/mammograms/{item.appointment_id}/record-medical-information/implanted-medical-device-history/{item.pk}/",
            "text": "Change",
            "visually_hidden_text": " item 2",
        }
