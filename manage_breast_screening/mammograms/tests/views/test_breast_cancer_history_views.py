import pytest
from django.contrib import messages
from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertMessages, assertRedirects

from manage_breast_screening.participants.tests.factories import AppointmentFactory


@pytest.mark.django_db
class TestBreastCancerHistoryViews:
    def test_renders_response(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:add_breast_cancer_history_item",
                kwargs={"pk": appointment.pk},
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_appointment(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_breast_cancer_history_item",
                kwargs={"pk": appointment.pk},
            ),
            {
                "diagnosis_location": "RIGHT_BREAST",
                "intervention_location": "NHS_HOSPITAL",
                "intervention_location_details_nhs_hospital": "abc",
                "left_breast_other_surgery": "NO_SURGERY",
                "left_breast_procedure": "NO_PROCEDURE",
                "left_breast_treatment": "NO_RADIOTHERAPY",
                "right_breast_other_surgery": "LYMPH_NODE_SURGERY",
                "right_breast_procedure": "LUMPECTOMY",
                "right_breast_treatment": "BREAST_RADIOTHERAPY",
                "systemic_treatments": "NO_SYSTEMIC_TREATMENTS",
            },
        )

        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": appointment.pk},
            ),
        )
        assertMessages(
            response,
            [
                messages.Message(
                    level=messages.SUCCESS,
                    message="Breast cancer history added",
                )
            ],
        )

    def test_invalid_post_renders_response_with_errors(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )

        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_breast_cancer_history_item",
                kwargs={"pk": appointment.pk},
            ),
            {},
        )

        assert response.status_code == 200
        assertInHTML(
            """
            <ul class="nhsuk-list nhsuk-error-summary__list">
                <li><a href="#id_diagnosis_location">Select which breasts cancer was diagnosed in</a></li>
                <li><a href="#id_right_breast_procedure">Select which procedure they have had in the right breast</a></li>
                <li><a href="#id_left_breast_procedure">Select which procedure they have had in the left breast</a></li>
                <li><a href="#id_right_breast_other_surgery">Select any other surgery they have had in the right breast</a></li>
                <li><a href="#id_left_breast_other_surgery">Select any other surgery they have had in the left breast</a></li>
                <li><a href="#id_right_breast_treatment">Select what treatment they have had in the right breast</a></li>
                <li><a href="#id_left_breast_treatment">Select what treatment they have had in the left breast</a></li>
                <li><a href="#id_systemic_treatments">Select what systemic treatments they have had</a></li>
                <li><a href="#id_intervention_location">Select where surgery and treatment took place</a></li>
            </ul>
            """,
            response.text,
        )
