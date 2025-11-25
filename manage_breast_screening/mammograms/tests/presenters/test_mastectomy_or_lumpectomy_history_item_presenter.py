from manage_breast_screening.mammograms.presenters.mastectomy_or_lumpectomy_history_item_presenter import (
    MastectomyOrLumpectomyHistoryItemPresenter,
)
from manage_breast_screening.participants.models.mastectomy_or_lumpectomy_history_item import (
    MastectomyOrLumpectomyHistoryItem,
)
from manage_breast_screening.participants.tests.factories import (
    MastectomyOrLumpectomyHistoryItemFactory,
)


class TestMastectomyOrLumpectomyHistoryItemPresenter:
    def test_single(self):
        item = MastectomyOrLumpectomyHistoryItemFactory.build(
            right_breast_procedure=MastectomyOrLumpectomyHistoryItem.Procedure.MASTECTOMY_NO_TISSUE_REMAINING,
            left_breast_procedure=MastectomyOrLumpectomyHistoryItem.Procedure.NO_PROCEDURE,
            right_breast_other_surgery=[
                MastectomyOrLumpectomyHistoryItem.Surgery.RECONSTRUCTION
            ],
            left_breast_other_surgery=[
                MastectomyOrLumpectomyHistoryItem.Surgery.NO_OTHER_SURGERY
            ],
            year_of_surgery=2018,
            surgery_reason=MastectomyOrLumpectomyHistoryItem.SurgeryReason.RISK_REDUCTION,
            additional_details="Right mastectomy with reconstruction",
        )

        presenter = MastectomyOrLumpectomyHistoryItemPresenter(item)

        assert presenter.summary_list_params == {
            "rows": [
                {
                    "key": {
                        "text": "Procedures",
                    },
                    "value": {
                        "html": "Right breast: Mastectomy (no tissue remaining)<br>Left breast: No procedure",
                    },
                },
                {
                    "key": {
                        "text": "Other surgery",
                    },
                    "value": {
                        "html": "Right breast: Reconstruction<br>Left breast: No other surgery",
                    },
                },
                {
                    "key": {
                        "text": "Year of surgery",
                    },
                    "value": {
                        "html": "2018",
                    },
                },
                {
                    "key": {
                        "text": "Surgery reason",
                    },
                    "value": {
                        "html": "Risk reduction",
                    },
                },
                {
                    "key": {
                        "text": "Surgery other reason details",
                    },
                    "value": {
                        "text": "",
                    },
                },
                {
                    "key": {
                        "text": "Additional details",
                    },
                    "value": {
                        "html": "Right mastectomy with reconstruction",
                    },
                },
            ],
        }
