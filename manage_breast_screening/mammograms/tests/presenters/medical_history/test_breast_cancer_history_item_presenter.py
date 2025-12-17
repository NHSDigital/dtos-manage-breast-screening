import pytest

from manage_breast_screening.mammograms.presenters.medical_history.breast_cancer_history_item_presenter import (
    BreastCancerHistoryItemPresenter,
)
from manage_breast_screening.participants.models.medical_history.breast_cancer_history_item import (
    BreastCancerHistoryItem,
)
from manage_breast_screening.participants.tests.factories import (
    BreastCancerHistoryItemFactory,
)


class TestBreastCancerHistoryItemPresenter:
    @pytest.fixture
    def item(self):
        return BreastCancerHistoryItemFactory.build(
            diagnosis_location=BreastCancerHistoryItem.DiagnosisLocationChoices.RIGHT_BREAST,
            right_breast_procedure=BreastCancerHistoryItem.Procedure.LUMPECTOMY,
            intervention_location=BreastCancerHistoryItem.InterventionLocation.NHS_HOSPITAL,
            intervention_location_details="East Tester Hospital",
            additional_details="some details",
        )

    @pytest.fixture
    def presenter(self, item):
        return BreastCancerHistoryItemPresenter(item)

    def test_attributes(self, presenter):
        assert presenter.cancer_location == "Right breast"
        assert presenter.right_breast_procedure == "Lumpectomy"
        assert presenter.left_breast_procedure == "No procedure"
        assert presenter.right_breast_other_surgery == ["No other surgery"]
        assert presenter.left_breast_other_surgery == ["No other surgery"]
        assert presenter.right_breast_treatments == ["No radiotherapy"]
        assert presenter.left_breast_treatments == ["No radiotherapy"]
        assert presenter.systemic_treatments == ["No systemic treatments"]
        assert presenter.additional_details == "some details"

    def test_change_link(self):
        item = BreastCancerHistoryItemFactory.build()

        presenter = BreastCancerHistoryItemPresenter(item)
        assert presenter.change_link == {
            "href": f"/mammograms/{item.appointment_id}/record-medical-information/breast-cancer-history/{item.pk}/",
            "text": "Change",
            "visually_hidden_text": " breast cancer item",
        }

    def test_change_link_with_counter(self):
        item = BreastCancerHistoryItemFactory.build()

        presenter = BreastCancerHistoryItemPresenter(item, counter=2)
        assert presenter.change_link == {
            "href": f"/mammograms/{item.appointment_id}/record-medical-information/breast-cancer-history/{item.pk}/",
            "text": "Change",
            "visually_hidden_text": " breast cancer item 2",
        }
