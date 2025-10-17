from datetime import datetime, timezone

import pytest

from manage_breast_screening.clinics.models import ClinicFilter
from manage_breast_screening.clinics.repositories.clinic_repository import (
    ClinicRepository,
)
from manage_breast_screening.clinics.tests.factories import (
    ClinicFactory,
    ProviderFactory,
)


@pytest.mark.django_db
class TestClinicRepositoryScopedQueryset:
    """Test that the repository correctly scopes clinics to the provider."""

    def test_list_returns_clinics_for_provider(self):
        provider = ProviderFactory.create()
        other_provider = ProviderFactory.create()

        # Create clinics for different providers
        clinic_for_provider = ClinicFactory.create(setting__provider=provider)
        clinic_for_other_provider = ClinicFactory.create(
            setting__provider=other_provider
        )

        repository = ClinicRepository(provider=provider)
        clinics = repository.list()

        assert clinic_for_provider in clinics
        assert clinic_for_other_provider not in clinics


@pytest.mark.django_db
class TestByFilter:
    """Test filtering clinics by date filter."""

    def test_filters_today_clinics(self):
        provider = ProviderFactory.create()

        today = datetime.now(timezone.utc).replace(hour=10, minute=0, second=0)
        tomorrow = today.replace(day=today.day + 1)
        yesterday = today.replace(day=today.day - 1)

        today_clinic = ClinicFactory.create(setting__provider=provider, starts_at=today)
        tomorrow_clinic = ClinicFactory.create(
            setting__provider=provider, starts_at=tomorrow
        )
        yesterday_clinic = ClinicFactory.create(
            setting__provider=provider, starts_at=yesterday
        )

        repository = ClinicRepository(provider=provider)
        clinics = list(repository.list(ClinicFilter.TODAY))

        assert today_clinic in clinics
        assert tomorrow_clinic not in clinics
        assert yesterday_clinic not in clinics


@pytest.mark.django_db
class TestWithSettings:
    """Test prefetch_related optimization for settings."""

    def test_prefetch_related_includes_settings(self, django_assert_num_queries):
        provider = ProviderFactory.create()
        ClinicFactory.create(setting__provider=provider)
        ClinicFactory.create(setting__provider=provider)

        repository = ClinicRepository(provider=provider)

        # Execute query with prefetch_related
        with django_assert_num_queries(2):  # 1 for clinics, 1 for prefetch settings
            clinics = list(repository.list())
            # Accessing setting should not trigger additional queries
            for clinic in clinics:
                _ = clinic.setting


@pytest.mark.django_db
class TestFilterCounts:
    """Test getting filter counts for clinics."""

    def test_returns_counts_for_each_filter_type(self):
        provider = ProviderFactory.create()
        other_provider = ProviderFactory.create()

        now = datetime.now(timezone.utc)
        today = now.replace(hour=10, minute=0, second=0, microsecond=0)
        upcoming = today.replace(day=today.day + 2)
        completed = today.replace(day=today.day - 2)

        # Create 2 today clinics for provider
        ClinicFactory.create(setting__provider=provider, starts_at=today)
        ClinicFactory.create(
            setting__provider=provider, starts_at=today.replace(hour=14)
        )

        # Create 3 upcoming clinics for provider
        ClinicFactory.create(setting__provider=provider, starts_at=upcoming)
        ClinicFactory.create(
            setting__provider=provider, starts_at=upcoming.replace(day=upcoming.day + 1)
        )
        ClinicFactory.create(
            setting__provider=provider, starts_at=upcoming.replace(day=upcoming.day + 2)
        )

        # Create 1 completed clinic for provider
        ClinicFactory.create(setting__provider=provider, starts_at=completed)

        # Create clinics for other provider (should not be counted)
        ClinicFactory.create(setting__provider=other_provider, starts_at=today)
        ClinicFactory.create(setting__provider=other_provider, starts_at=upcoming)

        repository = ClinicRepository(provider=provider)
        counts = repository.filter_counts()

        assert counts[ClinicFilter.ALL] == 6
        assert counts[ClinicFilter.TODAY] == 2
        assert counts[ClinicFilter.UPCOMING] == 3
        assert counts[ClinicFilter.COMPLETED] == 1
