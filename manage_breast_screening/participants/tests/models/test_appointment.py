import pytest

from manage_breast_screening.manual_images.tests.factories import (
    SeriesFactory,
    StudyFactory,
)
from manage_breast_screening.participants.tests.factories import AppointmentFactory


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
