import pytest

from manage_breast_screening.participants.models.appointment import (
    AppointmentStatusNames,
)
from manage_breast_screening.participants.tests.factories import AppointmentFactory


@pytest.fixture
def appointment(clinical_user_client):
    return AppointmentFactory.create(
        clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
    )


@pytest.fixture
def completed_appointment(clinical_user_client):
    return AppointmentFactory.create(
        current_status=AppointmentStatusNames.SCREENED,
        clinic_slot__clinic__setting__provider=clinical_user_client.current_provider,
    )


@pytest.fixture
def in_progress_appointment(clinical_user_client):
    return AppointmentFactory.create(
        current_status=AppointmentStatusNames.IN_PROGRESS,
        reinvite=False,
        clinic_slot__clinic__setting__provider=clinical_user_client.current_provider,
    )
