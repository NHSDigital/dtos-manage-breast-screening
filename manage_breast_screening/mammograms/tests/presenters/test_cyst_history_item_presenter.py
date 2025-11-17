from manage_breast_screening.mammograms.presenters.cyst_history_item_presenter import (
    CystHistoryItemPresenter,
)
from manage_breast_screening.participants.models.cyst_history_item import (
    CystHistoryItem,
)
from manage_breast_screening.participants.tests.factories import (
    CystHistoryItemFactory,
)


class TestCystHistoryItemPresenter:
    def test_single(self):
        item = CystHistoryItemFactory.build(
            treatment=CystHistoryItem.Treatment.NO_TREATMENT,
            additional_details="Some additional details",
        )

        presenter = CystHistoryItemPresenter(item)
        assert presenter.summary_list_params == {
            "rows": [
                {
                    "key": {
                        "text": "Treatment",
                    },
                    "value": {
                        "html": "No treatment",
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
