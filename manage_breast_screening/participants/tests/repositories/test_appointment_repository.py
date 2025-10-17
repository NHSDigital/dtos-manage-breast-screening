from datetime import datetime, timezone

import pytest

from manage_breast_screening.clinics.tests.factories import (
    ClinicFactory,
    ProviderFactory,
)
from manage_breast_screening.participants.models import Appointment, AppointmentStatus
from manage_breast_screening.participants.repositories.appointment_repository import (
    AppointmentRepository,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ParticipantFactory,
)


@pytest.mark.django_db
class TestList:
    def test_list_returns_appointments_for_clinic(self):
        provider = ProviderFactory.create()
        other_provider = ProviderFactory.create()
        clinic1 = ClinicFactory.create(setting__provider=provider)
        clinic2 = ClinicFactory.create(setting__provider=provider)
        clinic3 = ClinicFactory.create(setting__provider=other_provider)

        appointment1 = AppointmentFactory.create(
            clinic_slot__clinic=clinic1,
            clinic_slot__starts_at=datetime(2025, 1, 3, 10, 0, tzinfo=timezone.utc),
        )
        _appointment2 = AppointmentFactory.create(
            clinic_slot__clinic=clinic2,
            clinic_slot__starts_at=datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc),
        )
        _appointment3 = AppointmentFactory.create(
            clinic_slot__clinic=clinic3,
            clinic_slot__starts_at=datetime(2025, 1, 2, 10, 0, tzinfo=timezone.utc),
        )

        repository = AppointmentRepository(provider=provider)
        appointments = list(repository.list(clinic=clinic1))

        assert appointments == [appointment1]

    def test_orders_appointments(self):
        provider = ProviderFactory.create()
        clinic = ClinicFactory.create(setting__provider=provider)

        appointment1 = AppointmentFactory.create(
            clinic_slot__clinic=clinic,
            clinic_slot__starts_at=datetime(2025, 1, 3, 10, 0, tzinfo=timezone.utc),
        )
        appointment2 = AppointmentFactory.create(
            clinic_slot__clinic=clinic,
            clinic_slot__starts_at=datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc),
        )
        appointment3 = AppointmentFactory.create(
            clinic_slot__clinic=clinic,
            clinic_slot__starts_at=datetime(2025, 1, 2, 10, 0, tzinfo=timezone.utc),
        )

        repository = AppointmentRepository(provider=provider)
        appointments = list(repository.list(clinic=clinic))

        assert appointments == [appointment2, appointment3, appointment1]


@pytest.mark.django_db
class TestListForParticipant:
    def test_filters_appointments_for_specific_participant(self):
        provider = ProviderFactory.create()
        participant1 = ParticipantFactory.create()
        participant2 = ParticipantFactory.create()

        appointment1 = AppointmentFactory.create(
            screening_episode__participant=participant1,
            clinic_slot__clinic__setting__provider=provider,
        )
        appointment2 = AppointmentFactory.create(
            screening_episode__participant=participant2,
            clinic_slot__clinic__setting__provider=provider,
        )

        repository = AppointmentRepository(provider=provider)
        appointments = list(repository.list_for_participant(participant1))

        assert appointment1 in appointments
        assert appointment2 not in appointments

    def test_returns_empty_when_participant_has_no_appointments(self):
        provider = ProviderFactory.create()
        participant = ParticipantFactory.create()

        repository = AppointmentRepository(provider=provider)
        appointments = list(repository.list_for_participant(participant))

        assert len(appointments) == 0

    def test_orders_appointments_by_clinic_slot_starts_at_descending(self):
        provider = ProviderFactory.create()
        participant1 = ParticipantFactory.create()

        appointment1 = AppointmentFactory.create(
            screening_episode__participant=participant1,
            clinic_slot__clinic__setting__provider=provider,
            clinic_slot__starts_at=datetime(2025, 1, 3, 10, 0, tzinfo=timezone.utc),
        )
        appointment2 = AppointmentFactory.create(
            screening_episode__participant=participant1,
            clinic_slot__clinic__setting__provider=provider,
            clinic_slot__starts_at=datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc),
        )
        appointment3 = AppointmentFactory.create(
            screening_episode__participant=participant1,
            clinic_slot__clinic__setting__provider=provider,
            clinic_slot__starts_at=datetime(2025, 1, 2, 10, 0, tzinfo=timezone.utc),
        )

        repository = AppointmentRepository(provider=provider)
        appointments = list(repository.list_for_participant(participant1))

        assert appointments == [appointment1, appointment3, appointment2]


@pytest.mark.django_db
class TestShow:
    def test_returns_appointment(self):
        provider = ProviderFactory.create()
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=provider
        )

        repository = AppointmentRepository(provider=provider)
        result = repository.show(appointment.pk)

        assert result == appointment

    def test_raises_appointment_not_found_if_appointment_belongs_to_other_provider(
        self,
    ):
        provider = ProviderFactory.create()
        other_provider = ProviderFactory.create()
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=other_provider
        )

        repository = AppointmentRepository(provider=provider)
        with pytest.raises(Appointment.DoesNotExist):
            repository.show(appointment.pk)


@pytest.mark.django_db
class TestFilterCountsForClinic:
    """Test getting filter counts for a clinic."""

    def test_returns_counts_for_each_filter_type(self):
        provider = ProviderFactory.create()
        other_provider = ProviderFactory.create()

        clinic = ClinicFactory.create(setting__provider=provider)
        other_clinic = ClinicFactory.create(setting__provider=other_provider)

        # Create 2 CONFIRMED appointments (count as "remaining")
        AppointmentFactory.create(
            clinic_slot__clinic=clinic,
            current_status=AppointmentStatus.CONFIRMED,
        )
        AppointmentFactory.create(
            clinic_slot__clinic=clinic,
            current_status=AppointmentStatus.CONFIRMED,
        )

        # Create 2 CHECKED_IN appointments (count as both "remaining" and "checked_in")
        AppointmentFactory.create(
            clinic_slot__clinic=clinic,
            current_status=AppointmentStatus.CHECKED_IN,
        )
        AppointmentFactory.create(
            clinic_slot__clinic=clinic,
            current_status=AppointmentStatus.CHECKED_IN,
        )

        # Create 3 complete appointments
        AppointmentFactory.create(
            clinic_slot__clinic=clinic,
            current_status=AppointmentStatus.CANCELLED,
        )
        AppointmentFactory.create(
            clinic_slot__clinic=clinic,
            current_status=AppointmentStatus.SCREENED,
        )
        AppointmentFactory.create(
            clinic_slot__clinic=clinic,
            current_status=AppointmentStatus.DID_NOT_ATTEND,
        )

        # Create appointments for other clinic (should not be counted)
        AppointmentFactory.create(
            clinic_slot__clinic=other_clinic,
            current_status=AppointmentStatus.CONFIRMED,
        )
        AppointmentFactory.create(
            clinic_slot__clinic=other_clinic,
            current_status=AppointmentStatus.CHECKED_IN,
        )

        repository = AppointmentRepository(provider=provider)
        counts = repository.filter_counts_for_clinic(clinic)

        assert counts["all"] == 7
        assert counts["remaining"] == 4  # 2 confirmed + 2 checked_in
        assert counts["checked_in"] == 2
        assert counts["complete"] == 3  # cancelled + screened + did_not_attend
