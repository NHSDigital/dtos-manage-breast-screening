from datetime import date

import pytest
import time_machine

from manage_breast_screening.mammograms.presenters.medical_history.other_procedure_history_item_presenter import (
    OtherProcedureHistoryItemPresenter,
)
from manage_breast_screening.participants.models.medical_history.other_procedure_history_item import (
    OtherProcedureHistoryItem,
)
from manage_breast_screening.participants.tests.factories import (
    OtherProcedureHistoryItemFactory,
)


class TestOtherProcedureHistoryItemPresenter:
    @pytest.fixture
    def item(self):
        return OtherProcedureHistoryItemFactory.build(
            procedure=OtherProcedureHistoryItem.Procedure.BREAST_REDUCTION,
            procedure_details="Lorem ipsum dolor sit amet",
            procedure_year=2020,
            additional_details="Some additional details",
        )

    @pytest.fixture
    @time_machine.travel(date(2025, 1, 1))
    def presenter(self, item):
        return OtherProcedureHistoryItemPresenter(item)

    @time_machine.travel(date(2025, 1, 1))
    def test_attributes(self, presenter):
        assert presenter.type == {
            "type": "Breast reduction",
            "details": "Lorem ipsum dolor sit amet",
        }
        assert presenter.procedure_year == "2020 (5 years ago)"
        assert presenter.additional_details == "Some additional details"
