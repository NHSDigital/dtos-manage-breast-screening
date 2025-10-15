import pytest

from manage_breast_screening.clinics.tests.factories import ProviderFactory
from manage_breast_screening.participants.repositories.participant_repository import (
    ParticipantRepository,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ParticipantFactory,
)


@pytest.mark.django_db
def test_all_returns_participants_with_appointments_for_provider():
    provider = ProviderFactory.create()
    other_provider = ProviderFactory.create()

    participant_with_provider_appointment = ParticipantFactory.create()
    participant_without_provider_appointment = ParticipantFactory.create()
    participant_without_any_appointment = ParticipantFactory.create()

    AppointmentFactory.create(
        screening_episode__participant=participant_with_provider_appointment,
        clinic_slot__clinic__setting__provider=provider,
    )
    AppointmentFactory.create(
        screening_episode__participant=participant_without_provider_appointment,
        clinic_slot__clinic__setting__provider=other_provider,
    )

    repository = ParticipantRepository(provider=provider)

    participants = set(repository.all())

    assert participant_with_provider_appointment in participants
    assert participant_without_provider_appointment not in participants
    assert participant_without_any_appointment not in participants
