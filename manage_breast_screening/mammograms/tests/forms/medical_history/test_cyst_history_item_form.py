import pytest
from django.http import QueryDict

from manage_breast_screening.conftest import make_query_dict
from manage_breast_screening.participants.models.medical_history.cyst_history_item import (
    CystHistoryItem,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    CystHistoryItemFactory,
)

from ....forms.medical_history.cyst_history_item_form import CystHistoryItemForm


@pytest.mark.django_db
class TestCystHistoryForm:
    def test_no_data(self):
        appointment = AppointmentFactory()
        form = CystHistoryItemForm(QueryDict(), participant=appointment.participant)

        assert not form.is_valid()
        assert form.errors == {"treatment": ["Select the treatment type"]}

    @pytest.mark.parametrize(
        "data",
        [
            {
                "treatment": CystHistoryItem.Treatment.NO_TREATMENT,
            },
            {
                "treatment": CystHistoryItem.Treatment.DRAINAGE_OR_REMOVAL,
            },
            {
                "treatment": CystHistoryItem.Treatment.NO_TREATMENT,
                "additional_details": "Some additional details",
            },
            {
                "treatment": CystHistoryItem.Treatment.DRAINAGE_OR_REMOVAL,
                "additional_details": "Some additional details",
            },
        ],
    )
    def test_valid_create(self, data):
        appointment = AppointmentFactory()
        form = CystHistoryItemForm(
            make_query_dict(data),
            participant=appointment.participant,
        )

        assert form.is_valid()

        obj = form.create(appointment=appointment)

        assert obj.appointment == appointment
        assert obj.treatment == data.get("treatment")
        assert obj.additional_details == data.get("additional_details", "")

    @pytest.fixture
    def instance(self):
        return CystHistoryItemFactory(
            treatment=CystHistoryItem.Treatment.DRAINAGE_OR_REMOVAL
        )

    @pytest.mark.parametrize(
        "data",
        [
            {
                "treatment": CystHistoryItem.Treatment.NO_TREATMENT,
            },
            {
                "treatment": CystHistoryItem.Treatment.DRAINAGE_OR_REMOVAL,
            },
            {
                "treatment": CystHistoryItem.Treatment.NO_TREATMENT,
                "additional_details": "Some additional details",
            },
            {
                "treatment": CystHistoryItem.Treatment.DRAINAGE_OR_REMOVAL,
                "additional_details": "Some additional details",
            },
        ],
    )
    def test_valid_update(self, instance, data):
        form = CystHistoryItemForm(
            instance=instance,
            participant=instance.appointment.participant,
            data=make_query_dict(data),
        )

        assert form.is_valid()

        obj = form.update()
        assert obj.appointment == instance.appointment
        assert obj.treatment == data.get("treatment")
        assert obj.additional_details == data.get("additional_details", "")
