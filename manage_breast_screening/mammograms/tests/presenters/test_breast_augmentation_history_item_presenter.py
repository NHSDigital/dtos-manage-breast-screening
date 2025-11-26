from manage_breast_screening.mammograms.presenters.breast_augmentation_history_item_presenter import (
    BreastAugmentationHistoryItemPresenter,
)
from manage_breast_screening.participants.models.breast_augmentation_history_item import (
    BreastAugmentationHistoryItem,
)
from manage_breast_screening.participants.tests.factories import (
    BreastAugmentationHistoryItemFactory,
)


class TestBreastAugmentationHistoryItemPresenter:
    def test_single(self):
        item = BreastAugmentationHistoryItemFactory.build(
            right_breast_procedures=[
                BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
            ],
            procedure_year=2000,
            implants_have_been_removed=True,
            removal_year=2018,
            additional_details="some details",
        )

        presenter = BreastAugmentationHistoryItemPresenter(item)

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
                        "html": "2000",
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
            "href": f"/mammograms/{item.appointment_id}/record-medical-information/breast-augmentation-history/{item.pk}",
            "text": "Change",
            "visually_hidden_text": " breast implants or augmentation item",
        }

    def test_change_link_with_counter(self):
        item = BreastAugmentationHistoryItemFactory.build()

        presenter = BreastAugmentationHistoryItemPresenter(item, counter=2)
        assert presenter.change_link == {
            "href": f"/mammograms/{item.appointment_id}/record-medical-information/breast-augmentation-history/{item.pk}",
            "text": "Change",
            "visually_hidden_text": " breast implants or augmentation item 2",
        }
