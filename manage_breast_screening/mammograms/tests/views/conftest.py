import pytest

from manage_breast_screening.participants.models import AppointmentStatus
from manage_breast_screening.participants.tests.factories import AppointmentFactory


@pytest.fixture
def appointment(clinical_user_client):
    return AppointmentFactory.create(
        clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
    )


@pytest.fixture
def completed_appointment():
    return AppointmentFactory.create(current_status=AppointmentStatus.SCREENED)
