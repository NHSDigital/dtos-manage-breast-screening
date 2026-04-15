import pytest

from manage_breast_screening.mammograms.services.appointment_services import StepNames
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
        current_status__created_by=clinical_user_client.user,
        reinvite=False,
        clinic_slot__clinic__setting__provider=clinical_user_client.current_provider,
    )


@pytest.fixture
def confirmed_identity_appointment(clinical_user_client):
    appointment = AppointmentFactory.create(
        current_status=AppointmentStatusNames.IN_PROGRESS,
        current_status__created_by=clinical_user_client.user,
        clinic_slot__clinic__setting__provider=clinical_user_client.current_provider,
    )
    appointment.completed_workflow_steps.create(
        step_name=StepNames.CONFIRM_IDENTITY,
        created_by=clinical_user_client.user,
    )
    return appointment


@pytest.fixture
def reviewed_appointment(clinical_user_client):
    appointment = AppointmentFactory.create(
        current_status=AppointmentStatusNames.IN_PROGRESS,
        current_status__created_by=clinical_user_client.user,
        clinic_slot__clinic__setting__provider=clinical_user_client.current_provider,
    )
    appointment.completed_workflow_steps.create(
        step_name=StepNames.CONFIRM_IDENTITY,
        created_by=clinical_user_client.user,
    )
    appointment.completed_workflow_steps.create(
        step_name=StepNames.REVIEW_MEDICAL_INFORMATION,
        created_by=clinical_user_client.user,
    )
    return appointment


@pytest.fixture
def taken_images_appointment(clinical_user_client):
    appointment = AppointmentFactory.create(
        current_status=AppointmentStatusNames.IN_PROGRESS,
        current_status__created_by=clinical_user_client.user,
        clinic_slot__clinic__setting__provider=clinical_user_client.current_provider,
    )
    appointment.completed_workflow_steps.create(
        step_name=StepNames.CONFIRM_IDENTITY,
        created_by=clinical_user_client.user,
    )
    appointment.completed_workflow_steps.create(
        step_name=StepNames.REVIEW_MEDICAL_INFORMATION,
        created_by=clinical_user_client.user,
    )
    appointment.completed_workflow_steps.create(
        step_name=StepNames.TAKE_IMAGES,
        created_by=clinical_user_client.user,
    )
    return appointment
