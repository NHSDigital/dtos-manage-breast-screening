import pytest
from pytest_django.asserts import assertQuerySetEqual

from manage_breast_screening.manual_images.services import StudyService
from manage_breast_screening.participants.tests.factories import AppointmentFactory


@pytest.mark.django_db
class TestStudyService:
    def test_create_with_default_series(self, clinical_user):
        appointment = AppointmentFactory()
        service = StudyService(appointment=appointment, current_user=clinical_user)
        study = service.create_with_default_series()

        assertQuerySetEqual(
            study.series_set.values_list("view_position", "laterality", "count"),
            [("CC", "L", 1), ("CC", "R", 1), ("MLO", "L", 1), ("MLO", "R", 1)],
            ordered=False,
        )

    def test_create_with_existing_series(self, clinical_user):
        appointment = AppointmentFactory()
        service = StudyService(appointment=appointment, current_user=clinical_user)
        study = service.create_with_default_series()
        appointment.study.series_set.create(
            view_position="EKLUND", laterality="L", count=1
        )

        assertQuerySetEqual(
            study.series_set.values_list("view_position", "laterality", "count"),
            [
                ("CC", "L", 1),
                ("CC", "R", 1),
                ("MLO", "L", 1),
                ("MLO", "R", 1),
                ("EKLUND", "L", 1),
            ],
            ordered=False,
        )

        new_study = service.create_with_default_series()
        assertQuerySetEqual(
            new_study.series_set.values_list("view_position", "laterality", "count"),
            [("CC", "L", 1), ("CC", "R", 1), ("MLO", "L", 1), ("MLO", "R", 1)],
            ordered=False,
        )
