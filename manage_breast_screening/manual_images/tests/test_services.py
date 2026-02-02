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

    def test_create_with_default_series_when_existing_series(self, clinical_user):
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

    def test_create_with_given_counts_when_all_counts_greater_than_zero(
        self, clinical_user
    ):
        appointment = AppointmentFactory()
        service = StudyService(appointment=appointment, current_user=clinical_user)
        study = service.create(
            additional_details="Some details",
            series_data=[
                {"view_position": "CC", "laterality": "L", "count": 1},
                {"view_position": "CC", "laterality": "R", "count": 2},
                {"view_position": "MLO", "laterality": "L", "count": 3},
                {"view_position": "MLO", "laterality": "R", "count": 4},
                {"view_position": "EKLUND", "laterality": "L", "count": 5},
                {"view_position": "EKLUND", "laterality": "R", "count": 6},
            ],
        )

        assert study.additional_details == "Some details"
        assertQuerySetEqual(
            study.series_set.values_list("view_position", "laterality", "count"),
            [
                ("CC", "L", 1),
                ("CC", "R", 2),
                ("MLO", "L", 3),
                ("MLO", "R", 4),
                ("EKLUND", "L", 5),
                ("EKLUND", "R", 6),
            ],
            ordered=False,
        )

    def test_create_with_given_counts_when_some_counts_zero(self, clinical_user):
        appointment = AppointmentFactory()
        service = StudyService(appointment=appointment, current_user=clinical_user)
        study = service.create(
            additional_details="Some other details",
            series_data=[
                {"view_position": "CC", "laterality": "L", "count": 0},
                {"view_position": "CC", "laterality": "R", "count": 0},
                {"view_position": "MLO", "laterality": "L", "count": 0},
                {"view_position": "MLO", "laterality": "R", "count": 20},
                {"view_position": "EKLUND", "laterality": "L", "count": 0},
                {"view_position": "EKLUND", "laterality": "R", "count": 0},
            ],
        )

        assert study.additional_details == "Some other details"
        assertQuerySetEqual(
            study.series_set.values_list("view_position", "laterality", "count"),
            [
                ("MLO", "R", 20),
            ],
            ordered=False,
        )

    def test_create_with_given_series_when_existing_series(self, clinical_user):
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

        new_study = service.create(
            additional_details="Some more details",
            series_data=[
                {"view_position": "CC", "laterality": "L", "count": 7},
                {"view_position": "CC", "laterality": "R", "count": 0},
                {"view_position": "MLO", "laterality": "L", "count": 12},
                {"view_position": "MLO", "laterality": "R", "count": 15},
                {"view_position": "EKLUND", "laterality": "L", "count": 9},
                {"view_position": "EKLUND", "laterality": "R", "count": 6},
            ],
        )

        assert new_study.additional_details == "Some more details"
        assertQuerySetEqual(
            new_study.series_set.values_list("view_position", "laterality", "count"),
            [
                ("CC", "L", 7),
                ("MLO", "L", 12),
                ("MLO", "R", 15),
                ("EKLUND", "L", 9),
                ("EKLUND", "R", 6),
            ],
            ordered=False,
        )
