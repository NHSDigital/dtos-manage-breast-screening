import json

import pytest
from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertRedirects

from manage_breast_screening.participants.models.breast_features import (
    BreastFeatureAnnotation,
)


@pytest.mark.django_db
class TestRecordBreastFeaturesView:
    def test_get_renders_response(self, clinical_user_client, in_progress_appointment):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:record_breast_features",
                kwargs={"pk": in_progress_appointment.pk},
            )
        )
        assert response.status_code == 200

    @pytest.fixture
    def feature(self):
        return {"x": 0, "y": 0, "name": "abc", "id": "def"}

    def test_post_creates_annotation_if_it_does_not_exist(
        self, clinical_user_client, in_progress_appointment, feature
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:record_breast_features",
                kwargs={"pk": in_progress_appointment.pk},
            ),
            {"features": json.dumps([feature])},
        )

        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": in_progress_appointment.pk},
            ),
        )

        assert in_progress_appointment.breast_features.annotations_json == [feature]

    def test_post_updates_annotation_if_it_exists(
        self, clinical_user_client, in_progress_appointment, feature
    ):
        BreastFeatureAnnotation.objects.create(
            appointment=in_progress_appointment,
            annotations_json=[{"x": 1, "y": 1, "name": "old", "id": "old"}],
        )

        assert in_progress_appointment.breast_features

        response = clinical_user_client.http.post(
            reverse(
                "mammograms:record_breast_features",
                kwargs={"pk": in_progress_appointment.pk},
            ),
            {"features": json.dumps([feature])},
        )

        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": in_progress_appointment.pk},
            ),
        )

        in_progress_appointment.refresh_from_db()
        assert in_progress_appointment.breast_features.annotations_json == [feature]

    def test_invalid_post_renders_response_with_errors(
        self, clinical_user_client, in_progress_appointment
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:record_breast_features",
                kwargs={"pk": in_progress_appointment.pk},
            ),
            {
                "features": "abc",
            },
        )
        assert response.status_code == 200
        assertInHTML(
            """
            <ul class="nhsuk-list nhsuk-error-summary__list">
                <li><a href="#id_features">There was a problem saving the annotations</a></li>
            </ul>
            """,
            response.text,
        )
