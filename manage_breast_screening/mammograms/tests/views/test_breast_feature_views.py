import json

import pytest
from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertRedirects

from manage_breast_screening.participants.models.breast_features import (
    BreastFeatureAnnotation,
)


@pytest.mark.django_db
class TestUpsertBreastFeaturesView:
    def test_get_renders_response(
        self, clinical_user_client, confirmed_identity_appointment
    ):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:upsert_breast_features",
                kwargs={"pk": confirmed_identity_appointment.pk},
            )
        )
        assert response.status_code == 200

    @pytest.fixture
    def feature(self):
        return {"id": "scar", "region_id": "right_upper_outer", "x": 133, "y": 82}

    def test_post_creates_annotation_if_it_does_not_exist(
        self, clinical_user_client, confirmed_identity_appointment, feature
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:upsert_breast_features",
                kwargs={"pk": confirmed_identity_appointment.pk},
            ),
            {"features": json.dumps([feature])},
        )

        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": confirmed_identity_appointment.pk},
            ),
        )

        assert confirmed_identity_appointment.breast_features.annotations_json == [
            feature
        ]

    def test_post_updates_annotation_if_it_exists(
        self, clinical_user_client, confirmed_identity_appointment, feature
    ):
        BreastFeatureAnnotation.objects.create(
            appointment=confirmed_identity_appointment,
            annotations_json=[
                {"id": "mole", "region_id": "left_upper_inner", "x": 488, "y": 164}
            ],
        )

        assert confirmed_identity_appointment.breast_features

        response = clinical_user_client.http.post(
            reverse(
                "mammograms:upsert_breast_features",
                kwargs={"pk": confirmed_identity_appointment.pk},
            ),
            {"features": json.dumps([feature])},
        )

        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": confirmed_identity_appointment.pk},
            ),
        )

        confirmed_identity_appointment.refresh_from_db()
        assert confirmed_identity_appointment.breast_features.annotations_json == [
            feature
        ]

    def test_invalid_post_renders_response_with_errors(
        self, clinical_user_client, confirmed_identity_appointment
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:upsert_breast_features",
                kwargs={"pk": confirmed_identity_appointment.pk},
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

    def test_identity_confirmed_step_incomplete(
        self, clinical_user_client, in_progress_appointment
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:upsert_breast_features",
                kwargs={"pk": in_progress_appointment.pk},
            )
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:show_appointment",
                kwargs={"pk": in_progress_appointment.pk},
            ),
        )
