from datetime import datetime
from datetime import timezone as tz

import pytest

from manage_breast_screening.clinics.models import Provider

from ..services import fetch_current_provider
from .factories import AppointmentFactory, ParticipantFactory, ScreeningEpisodeFactory


@pytest.mark.django_db
def test_fetch_current_provider():
    participant = ParticipantFactory.create()
    old_appointment = AppointmentFactory.create(
        screening_episode=ScreeningEpisodeFactory.create(participant=participant),
        starts_at=datetime(2022, 1, 1, 10, tzinfo=tz.utc),
    )
    new_appointment = AppointmentFactory.create(
        screening_episode=ScreeningEpisodeFactory.create(participant=participant),
        starts_at=datetime(2025, 2, 1, 10, tzinfo=tz.utc),
    )
    expected_current_provider = new_appointment.clinic_slot.clinic.setting.provider
    assert (
        expected_current_provider != old_appointment.clinic_slot.clinic.setting.provider
    )

    current_provider = fetch_current_provider(participant.pk)
    assert current_provider == expected_current_provider


@pytest.mark.django_db
def test_no_current_provider():
    participant = ParticipantFactory.create()

    with pytest.raises(Provider.DoesNotExist):
        fetch_current_provider(participant.pk)
