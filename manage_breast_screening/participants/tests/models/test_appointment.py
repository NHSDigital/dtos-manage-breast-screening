from datetime import date, datetime

import pytest
from django.utils import timezone

from manage_breast_screening.manual_images.tests.factories import (
    SeriesFactory,
    StudyFactory,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ParticipantReportedMammogramFactory,
)


@pytest.mark.django_db
class TestSeries:
    def test_returns_series_when_study_exists(self):
        appointment = AppointmentFactory.create()
        study = StudyFactory.create(appointment=appointment)
        series = SeriesFactory.create(study=study)

        result = appointment.series()

        assert list(result) == [series]

    def test_returns_empty_queryset_when_no_study(self):
        appointment = AppointmentFactory.create()

        result = appointment.series()

        assert result.exists() is False

    def test_has_study_true(self):
        appointment = AppointmentFactory.create()
        StudyFactory.create(appointment=appointment)

        assert appointment.has_study() is True

    def test_has_study_false(self):
        appointment = AppointmentFactory.create()

        assert appointment.has_study() is False


@pytest.mark.django_db
class TestRecentReportedMammograms:
    def test_returns_empty_queryset_when_no_mammograms(self):
        appointment = AppointmentFactory.create()

        result = appointment.recent_reported_mammograms()

        assert result.exists() is False

    def test_returns_all_mammograms_when_no_since_date(self):
        appointment = AppointmentFactory.create()
        long_time_ago = self.create_mammogram_with_created_at(
            appointment=appointment,
            created_at=timezone.make_aware(datetime(1970, 6, 15)),
        )
        years_ago = self.create_mammogram_with_created_at(
            appointment=appointment,
            created_at=timezone.make_aware(datetime(2020, 10, 22)),
        )
        today = self.create_mammogram_with_created_at(
            appointment=appointment,
            created_at=timezone.make_aware(datetime.now()),
        )

        result = appointment.recent_reported_mammograms()

        assert list(result) == [today, years_ago, long_time_ago]

    def test_returns_mammograms_since_date(self):
        appointment = AppointmentFactory.create()
        on_since_date = self.create_mammogram_with_created_at(
            appointment=appointment,
            created_at=timezone.make_aware(datetime(2023, 6, 15)),
        )
        day_before = self.create_mammogram_with_created_at(
            appointment=appointment,
            created_at=timezone.make_aware(datetime(2023, 6, 14)),
        )
        day_after = self.create_mammogram_with_created_at(
            appointment=appointment,
            created_at=timezone.make_aware(datetime(2023, 6, 16)),
        )
        year_before = self.create_mammogram_with_created_at(
            appointment=appointment,
            created_at=timezone.make_aware(datetime(2022, 12, 31)),
        )
        year_after = self.create_mammogram_with_created_at(
            appointment=appointment,
            created_at=timezone.make_aware(datetime(2024, 1, 1)),
        )
        today = self.create_mammogram_with_created_at(
            appointment=appointment,
            created_at=timezone.make_aware(datetime.now()),
        )

        result = appointment.recent_reported_mammograms(since_date=date(2023, 6, 15))

        assert list(result) == [today, year_after, day_after]
        assert on_since_date not in result
        assert day_before not in result
        assert year_before not in result

    def test_returns_mammograms_with_same_created_at(self):
        appointment = AppointmentFactory.create()
        duplicate_1 = self.create_mammogram_with_created_at(
            appointment=appointment,
            created_at=timezone.make_aware(datetime(2020, 8, 12)),
        )
        duplicate_2 = self.create_mammogram_with_created_at(
            appointment=appointment,
            created_at=timezone.make_aware(datetime(2020, 8, 12)),
        )

        result = appointment.recent_reported_mammograms()

        assert len(result) == 2
        assert set(result) == {duplicate_1, duplicate_2}

    def create_mammogram_with_created_at(self, appointment, created_at):
        mammogram = ParticipantReportedMammogramFactory.create(appointment=appointment)
        mammogram.created_at = created_at
        mammogram.save()
        return mammogram
