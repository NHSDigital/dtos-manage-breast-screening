from manage_breast_screening.mammograms.presenters.other_procedure_history_item_presenter import (
    OtherProcedureHistoryItemPresenter,
)
from manage_breast_screening.participants.models.other_procedure_history_item import (
    OtherProcedureHistoryItem,
)
from manage_breast_screening.participants.tests.factories import (
    OtherProcedureHistoryItemFactory,
)


class TestOtherProcedureHistoryItemPresenter:
    def test_single(self):
        item = OtherProcedureHistoryItemFactory.build(
            procedure=OtherProcedureHistoryItem.Procedure.BREAST_REDUCTION,
            procedure_details="Lorem ipsum dolor sit amet",
            procedure_year=2020,
            additional_details="Some additional details",
        )

        presenter = OtherProcedureHistoryItemPresenter(item)
        assert presenter.summary_list_params == {
            "rows": [
                {
                    "key": {
                        "text": "Procedure",
                    },
                    "value": {
                        "html": "Breast reduction",
                    },
                },
                {
                    "key": {
                        "text": "Procedure details",
                    },
                    "value": {
                        "html": "Lorem ipsum dolor sit amet",
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
                        "text": "Additional details",
                    },
                    "value": {
                        "html": "Some additional details",
                    },
                },
            ],
        }
