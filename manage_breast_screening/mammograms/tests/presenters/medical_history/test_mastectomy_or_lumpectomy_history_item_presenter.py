import pytest

from manage_breast_screening.mammograms.presenters.medical_history.mastectomy_or_lumpectomy_history_item_presenter import (
    MastectomyOrLumpectomyHistoryItemPresenter,
)
from manage_breast_screening.participants.models.medical_history.mastectomy_or_lumpectomy_history_item import (
    MastectomyOrLumpectomyHistoryItem,
)
from manage_breast_screening.participants.tests.factories import (
    MastectomyOrLumpectomyHistoryItemFactory,
)


class TestMastectomyOrLumpectomyHistoryItemPresenter:
    @pytest.fixture
    def item(self):
        return MastectomyOrLumpectomyHistoryItemFactory.build(
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

    @pytest.fixture
    def presenter(self, item):
        return MastectomyOrLumpectomyHistoryItemPresenter(item)

    def test_attributes(self, presenter):
        assert presenter.right_breast_procedure == "Mastectomy (no tissue remaining)"
        assert presenter.left_breast_procedure == "No procedure"
        assert presenter.right_breast_other_surgery == ["Reconstruction"]
        assert presenter.left_breast_other_surgery == ["No other surgery"]
        assert presenter.year_of_surgery == "2018"
        assert presenter.surgery_reason == "Risk reduction"
        assert presenter.additional_details == "Right mastectomy with reconstruction"

    def test_change_link(self):
        item = MastectomyOrLumpectomyHistoryItemFactory.build(
            additional_details="Some additional details",
        )

        presenter = MastectomyOrLumpectomyHistoryItemPresenter(item)
        assert presenter.change_link == {
            "href": f"/mammograms/{item.appointment_id}/record-medical-information/mastectomy-or-lumpectomy-history/{item.pk}/",
            "text": "Change",
            "visually_hidden_text": " mastectomy or lumpectomy item",
        }

    def test_change_link_with_counter(self):
        item = MastectomyOrLumpectomyHistoryItemFactory.build(
            additional_details="Some additional details",
        )

        presenter = MastectomyOrLumpectomyHistoryItemPresenter(item, counter=2)
        assert presenter.change_link == {
            "href": f"/mammograms/{item.appointment_id}/record-medical-information/mastectomy-or-lumpectomy-history/{item.pk}/",
            "text": "Change",
            "visually_hidden_text": " mastectomy or lumpectomy item 2",
        }
