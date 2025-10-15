from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

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
class TestAppointmentRepositoryScopedQueryset:
    """Test that the repository correctly scopes appointments to the provider."""

    def test_all_returns_appointments_for_provider(self):
        provider = ProviderFactory.create()
        other_provider = ProviderFactory.create()

        # Create appointments for different providers
        appointment_for_provider = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=provider
        )
        appointment_for_other_provider = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=other_provider
        )

        repository = AppointmentRepository(provider=provider)
        appointments = repository.all()

        assert appointment_for_provider in appointments
        assert appointment_for_other_provider not in appointments


@pytest.mark.django_db
class TestOrderedByClinicSlotStartsAt:
    """Test ordering appointments by clinic slot start time."""

    def test_orders_appointments(self):
        provider = ProviderFactory.create()

        appointment1 = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=provider,
            clinic_slot__starts_at=datetime(2025, 1, 3, 10, 0, tzinfo=timezone.utc),
        )
        appointment2 = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=provider,
            clinic_slot__starts_at=datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc),
        )
        appointment3 = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=provider,
            clinic_slot__starts_at=datetime(2025, 1, 2, 10, 0, tzinfo=timezone.utc),
        )

        repository = AppointmentRepository(provider=provider)
        appointments = list(repository.ordered_by_clinic_slot_starts_at().all())
        appointments_descending = list(
            repository.ordered_by_clinic_slot_starts_at(descending=True).all()
        )

        assert appointments == [appointment2, appointment3, appointment1]
        assert appointments_descending == [appointment1, appointment3, appointment2]


@pytest.mark.django_db
class TestForParticipant:
    """Test filtering appointments by participant."""

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
        appointments = list(repository.for_participant(participant1).all())

        assert appointment1 in appointments
        assert appointment2 not in appointments

    def test_returns_empty_when_participant_has_no_appointments(self):
        provider = ProviderFactory.create()
        participant = ParticipantFactory.create()

        repository = AppointmentRepository(provider=provider)
        appointments = list(repository.for_participant(participant).all())

        assert len(appointments) == 0


@pytest.mark.django_db
class TestForClinicAndFilter:
    """Test filtering appointments by clinic and status filter."""

    def test_filters_appointments(self):
        provider = ProviderFactory.create()
        clinic = ClinicFactory.create(setting__provider=provider)

        confirmed_appointment = AppointmentFactory.create(
            clinic_slot__clinic=clinic,
            current_status=AppointmentStatus.CONFIRMED,
        )
        checked_in_appointment = AppointmentFactory.create(
            clinic_slot__clinic=clinic,
            current_status=AppointmentStatus.CHECKED_IN,
        )
        screened_appointment = AppointmentFactory.create(
            clinic_slot__clinic=clinic,
            current_status=AppointmentStatus.SCREENED,
        )

        repository = AppointmentRepository(provider=provider)
        appointments = list(repository.for_clinic_and_filter(clinic, "remaining").all())

        assert confirmed_appointment in appointments
        assert checked_in_appointment in appointments
        assert screened_appointment not in appointments


@pytest.mark.django_db
class TestWithSetting:
    """Test select_related optimization for clinic settings."""

    def test_select_related_includes_setting(self, django_assert_num_queries):
        provider = ProviderFactory.create()
        AppointmentFactory.create(clinic_slot__clinic__setting__provider=provider)

        repository = AppointmentRepository(provider=provider)

        # Execute query with select_related
        with django_assert_num_queries(1):
            appointment = repository.with_setting().all().first()
            # Accessing setting should not trigger additional query
            _ = appointment.clinic_slot.clinic.setting


@pytest.mark.django_db
class TestWithFullDetails:
    """Test select_related optimization for full appointment details."""

    def test_select_related_includes_full_details(self, django_assert_num_queries):
        provider = ProviderFactory.create()
        AppointmentFactory.create(clinic_slot__clinic__setting__provider=provider)

        repository = AppointmentRepository(provider=provider)

        # Execute query with full details
        with django_assert_num_queries(1):
            appointment = repository.with_full_details().all().first()
            # Accessing related objects should not trigger additional queries
            _ = appointment.clinic_slot.clinic
            _ = appointment.screening_episode.participant
            _ = appointment.screening_episode.participant.address


@pytest.mark.django_db
class TestWithListDetails:
    """Test prefetch and select_related optimization for list views."""

    def test_prefetch_and_select_related_includes_list_details(
        self, django_assert_num_queries
    ):
        provider = ProviderFactory.create()
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=provider
        )
        # Create multiple statuses to test prefetch
        AppointmentStatus.objects.create(
            appointment=appointment, state=AppointmentStatus.CHECKED_IN
        )

        repository = AppointmentRepository(provider=provider)

        # Execute query with list details
        with django_assert_num_queries(2):  # 1 for appointment, 1 for prefetch statuses
            appointment = repository.with_list_details().all().first()
            # Accessing related objects should not trigger additional queries
            _ = appointment.clinic_slot.clinic
            _ = appointment.screening_episode.participant
            _ = list(appointment.statuses.all())


@pytest.mark.django_db
class TestFilterCountsForClinic:
    """Test getting filter counts for a clinic."""

    def test_delegates_to_model_manager(self):
        provider = ProviderFactory.build()
        clinic = MagicMock()

        with patch.object(
            Appointment.objects, "filter_counts_for_clinic"
        ) as mock_filter_counts:
            repository = AppointmentRepository(provider=provider)
            repository.filter_counts_for_clinic(clinic)

            mock_filter_counts.assert_called_once_with(clinic)
