import pytest

from manage_breast_screening.participants.models import AppointmentStatus
from manage_breast_screening.participants.tests.factories import AppointmentFactory


@pytest.fixture
def appointment():
    return AppointmentFactory.create()


@pytest.fixture
def completed_appointment():
    return AppointmentFactory.create(current_status=AppointmentStatus.SCREENED)
