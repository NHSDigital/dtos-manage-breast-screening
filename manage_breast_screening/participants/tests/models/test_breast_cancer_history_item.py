import pytest
from django.forms import ValidationError

from manage_breast_screening.participants.models.breast_cancer_history_item import (
    BreastCancerHistoryItem,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    BreastCancerHistoryItemFactory,
)


@pytest.mark.django_db
class TestBreastCancerHistoryItem:
    def test_invalid_no_surgery(self):
        appointment = AppointmentFactory.create()
        item = BreastCancerHistoryItemFactory.build(
            appointment=appointment,
            left_breast_other_surgery=[
                BreastCancerHistoryItem.Surgery.NO_SURGERY,
                BreastCancerHistoryItem.Surgery.LYMPH_NODE_SURGERY,
            ],
        )

        with pytest.raises(
            ValidationError,
            match=r"\['Unselect \"No other surgery\" in order to select other options'\]",
        ):
            item.full_clean()

    def test_invalid_no_treatment(self):
        appointment = AppointmentFactory.create()
        item = BreastCancerHistoryItemFactory.build(
            appointment=appointment,
            right_breast_treatment=[
                BreastCancerHistoryItem.Treatment.BREAST_RADIOTHERAPY,
                BreastCancerHistoryItem.Treatment.NO_RADIOTHERAPY,
            ],
        )

        with pytest.raises(
            ValidationError,
            match=r"\['Unselect \"No radiotherapy\" in order to select other options'\]",
        ):
            item.full_clean()
