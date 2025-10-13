import pytest

from manage_breast_screening.participants.models import AppointmentStatus
from manage_breast_screening.participants.tests.factories import AppointmentFactory


@pytest.fixture
def appointment_viewed_by_clinical_user(clinical_user):
    return AppointmentFactory.create(
        clinic_slot__clinic__setting__provider=clinical_user.assignments.first().provider
    )


@pytest.fixture
def completed_appointment_viewed_by_clinical_user(clinical_user):
    return AppointmentFactory.create(
        clinic_slot__clinic__setting__provider=clinical_user.assignments.first().provider,
        current_status=AppointmentStatus.SCREENED,
    )


@pytest.fixture
def appointment_viewed_by_administrative_user(administrative_user):
    return AppointmentFactory.create(
        clinic_slot__clinic__setting__provider=administrative_user.assignments.first().provider
    )


@pytest.fixture
def completed_appointment_viewed_by_administrative_user(administrative_user):
    return AppointmentFactory.create(
        clinic_slot__clinic__setting__provider=administrative_user.assignments.first().provider,
        current_status=AppointmentStatus.SCREENED,
    )
