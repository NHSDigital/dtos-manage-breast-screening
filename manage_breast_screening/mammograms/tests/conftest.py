import pytest

from manage_breast_screening.participants.models.appointment import (
    AppointmentStatusNames,
)
from manage_breast_screening.participants.tests.factories import AppointmentFactory


@pytest.fixture
def in_progress_appointment():
    return AppointmentFactory.create(
        current_status=AppointmentStatusNames.IN_PROGRESS, reinvite=False
    )
