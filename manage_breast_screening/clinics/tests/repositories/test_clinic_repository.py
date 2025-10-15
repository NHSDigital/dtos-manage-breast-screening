from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from manage_breast_screening.clinics.models import Clinic, ClinicFilter
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

    def test_all_returns_clinics_for_provider(self):
        provider = ProviderFactory.create()
        other_provider = ProviderFactory.create()

        # Create clinics for different providers
        clinic_for_provider = ClinicFactory.create(setting__provider=provider)
        clinic_for_other_provider = ClinicFactory.create(
            setting__provider=other_provider
        )

        repository = ClinicRepository(provider=provider)
        clinics = repository.all()

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
        clinics = list(repository.by_filter(ClinicFilter.TODAY).all())

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
            clinics = list(repository.with_settings().all())
            # Accessing setting should not trigger additional queries
            for clinic in clinics:
                _ = clinic.setting


@pytest.mark.django_db
class TestFilterCounts:
    """Test getting filter counts for clinics."""

    def test_delegates_to_model_class_method(self):
        provider = ProviderFactory.build()

        with patch.object(Clinic, "filter_counts") as mock_filter_counts:
            repository = ClinicRepository(provider=provider)
            repository.filter_counts()

            mock_filter_counts.assert_called_once_with(provider.pk)
