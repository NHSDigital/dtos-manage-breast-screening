from datetime import date

import pytest
import time_machine

from manage_breast_screening.mammograms.presenters.medical_history.breast_augmentation_history_item_presenter import (
    BreastAugmentationHistoryItemPresenter,
)
from manage_breast_screening.participants.models.medical_history.breast_augmentation_history_item import (
    BreastAugmentationHistoryItem,
)
from manage_breast_screening.participants.tests.factories import (
    BreastAugmentationHistoryItemFactory,
)


class TestBreastAugmentationHistoryItemPresenter:
    @pytest.fixture
    def item(self):
        return BreastAugmentationHistoryItemFactory.build(
            right_breast_procedures=[
                BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
            ],
            procedure_year=2000,
            implants_have_been_removed=True,
            removal_year=2018,
            additional_details="some details",
        )

    @pytest.fixture
    @time_machine.travel(date(2025, 1, 1))
    def presenter(self, item):
        return BreastAugmentationHistoryItemPresenter(item)

    @time_machine.travel(date(2025, 1, 1))
    def test_attributes(self, presenter):
        assert presenter.right_breast_procedures == [
            "Breast implants (silicone or saline)"
        ]
        assert presenter.left_breast_procedures == ["No procedures"]
        assert presenter.procedure_year == "2000 (25 years ago)"
        assert presenter.implants_have_been_removed == "Yes (2018)"
        assert presenter.additional_details == "some details"

    @time_machine.travel(date(2025, 1, 1))
    def test_procedure_year_with_removal(self, presenter):
        assert presenter.procedure_year_with_removal == (
            "Implanted in 2000 (25 years ago)<br>Implants removed in 2018 (7 years ago)"
        )

    @time_machine.travel(date(2025, 1, 1))
    def test_single(self, presenter):
        assert presenter.summary_list_params == {
            "rows": [
                {
                    "key": {
                        "text": "Procedures",
                    },
                    "value": {
                        "html": "Right breast: Breast implants (silicone or saline)<br>Left breast: No procedures",
                    },
                },
                {
                    "key": {
                        "text": "Procedure year",
                    },
                    "value": {
                        "html": "2000 (25 years ago)",
                    },
                },
                {
                    "key": {
                        "text": "Implants have been removed",
                    },
                    "value": {
                        "html": "Yes (2018)",
                    },
                },
                {
                    "key": {
                        "text": "Additional details",
                    },
                    "value": {
                        "html": "some details",
                    },
                },
            ],
        }

    def test_change_link(self):
        item = BreastAugmentationHistoryItemFactory.build()

        presenter = BreastAugmentationHistoryItemPresenter(item)
        assert presenter.change_link == {
            "href": f"/mammograms/{item.appointment_id}/record-medical-information/breast-augmentation-history/{item.pk}/",
            "text": "Change",
            "visually_hidden_text": " breast implants or augmentation item",
        }

    def test_change_link_with_counter(self):
        item = BreastAugmentationHistoryItemFactory.build()

        presenter = BreastAugmentationHistoryItemPresenter(item, counter=2)
        assert presenter.change_link == {
            "href": f"/mammograms/{item.appointment_id}/record-medical-information/breast-augmentation-history/{item.pk}/",
            "text": "Change",
            "visually_hidden_text": " breast implants or augmentation item 2",
        }
