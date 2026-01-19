from datetime import date

import pytest
import time_machine

from manage_breast_screening.mammograms.presenters.medical_history.benign_lump_history_item_presenter import (
    BenignLumpHistoryItemPresenter,
)
from manage_breast_screening.participants.models.medical_history.benign_lump_history_item import (
    BenignLumpHistoryItem,
)
from manage_breast_screening.participants.tests.factories import (
    BenignLumpHistoryItemFactory,
)


class TestBenignLumpHistoryItemPresenter:
    @pytest.fixture
    def item(self):
        return BenignLumpHistoryItemFactory.build(
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

    @pytest.fixture
    @time_machine.travel(date(2025, 1, 1))
    def presenter(self, item):
        return BenignLumpHistoryItemPresenter(item)

    @time_machine.travel(date(2025, 1, 1))
    def test_attributes(self, presenter):
        assert presenter.right_breast_procedures == ["Needle biopsy", "Lump removed"]
        assert presenter.left_breast_procedures == ["No procedures"]
        assert presenter.procedure_year == "2015 (10 years ago)"
        assert presenter.treatment_location == {
            "type": "At a private clinic in the UK",
            "details": "Harley Street Clinic",
        }
        assert presenter.additional_details == "First line<br>Second line"

    def test_change_link(self):
        item = BenignLumpHistoryItemFactory.build()
        presenter = BenignLumpHistoryItemPresenter(item)

        result = presenter.change_link
        assert result == {
            "href": f"/mammograms/{item.appointment_id}/record-medical-information/benign-lump-history/{item.id}/",
            "text": "Change",
        }
