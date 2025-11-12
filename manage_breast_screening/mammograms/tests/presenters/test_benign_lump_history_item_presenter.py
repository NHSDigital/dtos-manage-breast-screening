from manage_breast_screening.mammograms.presenters.benign_lump_history_item_presenter import (
    BenignLumpHistoryItemPresenter,
)
from manage_breast_screening.participants.models.benign_lump_history_item import (
    BenignLumpHistoryItem,
)
from manage_breast_screening.participants.tests.factories import (
    BenignLumpHistoryItemFactory,
)


class TestBenignLumpHistoryItemPresenter:
    def test_summary_list_params(self):
        item = BenignLumpHistoryItemFactory.build(
            right_breast_procedures=[
                BenignLumpHistoryItem.Procedure.NEEDLE_BIOPSY,
                BenignLumpHistoryItem.Procedure.LUMP_REMOVED,
            ],
            left_breast_procedures=[BenignLumpHistoryItem.Procedure.NO_PROCEDURES],
            procedure_year=2015,
            procedure_location=BenignLumpHistoryItem.ProcedureLocation.PRIVATE_CLINIC_UK,
            procedure_location_details="Harley Street Clinic",
            additional_details="First line\nSecond line",
        )

        presenter = BenignLumpHistoryItemPresenter(item)

        assert presenter.summary_list_params == {
            "rows": [
                {
                    "key": {"text": "Procedures"},
                    "value": {
                        "html": (
                            "Right breast: Needle biopsy, Lump removed<br>"
                            "Left breast: No procedures"
                        )
                    },
                },
                {
                    "key": {"text": "Procedure year"},
                    "value": {"html": "2015"},
                },
                {
                    "key": {"text": "Procedure location"},
                    "value": {
                        "html": ("At a private clinic in the UK: Harley Street Clinic")
                    },
                },
                {
                    "key": {"text": "Additional details"},
                    "value": {"html": "First line<br>Second line"},
                },
            ],
        }
