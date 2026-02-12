import pytest
from django.urls import reverse
from pytest_django.asserts import assertInHTML

from manage_breast_screening.manual_images.tests.factories import (
    SeriesFactory,
    StudyFactory,
)


@pytest.mark.django_db
class TestShowAppointment:
    def test_renders_response(self, clinical_user_client, in_progress_appointment):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:show_appointment",
                kwargs={"pk": in_progress_appointment.pk},
            )
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestImages:
    def test_renders_view_counts(self, clinical_user_client, completed_appointment):
        study = StudyFactory(appointment=completed_appointment)
        SeriesFactory(study=study, view_position="MLO", laterality="R", count=1)
        SeriesFactory(study=study, view_position="CC", laterality="R", count=1)
        SeriesFactory(study=study, view_position="MLO", laterality="L", count=1)

        response = clinical_user_client.http.get(
            reverse(
                "mammograms:appointment_image_details",
                kwargs={"pk": completed_appointment.pk},
            )
        )
        assert response.status_code == 200
        assertInHTML("1× RMLO", response.text)
        assertInHTML("1× RCC", response.text)
        assertInHTML("1× LMLO", response.text)
        assertInHTML("0× LCC", response.text)
