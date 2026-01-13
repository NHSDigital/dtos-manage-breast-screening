import pytest

from manage_breast_screening.mammograms.presenters.medical_history.cyst_history_item_presenter import (
    CystHistoryItemPresenter,
)
from manage_breast_screening.participants.models.medical_history.cyst_history_item import (
    CystHistoryItem,
)
from manage_breast_screening.participants.tests.factories import CystHistoryItemFactory


class TestCystHistoryItemPresenter:
    @pytest.fixture
    def item(self):
        return CystHistoryItemFactory.build(
            treatment=CystHistoryItem.Treatment.NO_TREATMENT,
            additional_details="Some additional details",
        )

    @pytest.fixture
    def presenter(self, item):
        return CystHistoryItemPresenter(item)

    def test_attributes(self, presenter):
        assert presenter.treatment == "No treatment"
        assert presenter.additional_details == "Some additional details"

    def test_change_link(self):
        item = CystHistoryItemFactory.build(
            treatment=CystHistoryItem.Treatment.NO_TREATMENT,
            additional_details="Some additional details",
        )

        presenter = CystHistoryItemPresenter(item)
        assert presenter.change_link == {
            "href": f"/mammograms/{item.appointment_id}/record-medical-information/cyst-history/{item.pk}/",
            "text": "Change",
            "visually_hidden_text": " cyst item",
        }

    def test_change_link_with_counter(self):
        item = CystHistoryItemFactory.build(
            treatment=CystHistoryItem.Treatment.NO_TREATMENT,
            additional_details="Some additional details",
        )

        presenter = CystHistoryItemPresenter(item, counter=2)
        assert presenter.change_link == {
            "href": f"/mammograms/{item.appointment_id}/record-medical-information/cyst-history/{item.pk}/",
            "text": "Change",
            "visually_hidden_text": " cyst item 2",
        }
