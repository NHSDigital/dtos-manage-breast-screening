import pytest
from django.contrib import messages
from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertMessages, assertRedirects

from manage_breast_screening.participants.models.medical_history.breast_cancer_history_item import (
    BreastCancerHistoryItem,
)
from manage_breast_screening.participants.tests.factories import (
    BreastCancerHistoryItemFactory,
)


@pytest.fixture
def history_item(confirmed_identity_appointment):
    return BreastCancerHistoryItemFactory.create(
        appointment=confirmed_identity_appointment
    )


@pytest.mark.django_db
class TestBreastCancerHistoryView:
    def test_renders_response(
        self, clinical_user_client, confirmed_identity_appointment
    ):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:add_breast_cancer_history_item",
                kwargs={"pk": confirmed_identity_appointment.pk},
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_appointment(
        self, clinical_user_client, confirmed_identity_appointment
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_breast_cancer_history_item",
                kwargs={"pk": confirmed_identity_appointment.pk},
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
                kwargs={"pk": confirmed_identity_appointment.pk},
            ),
        )
        assertMessages(
            response,
            [
                messages.Message(
                    level=messages.SUCCESS,
                    message="Added breast cancer",
                )
            ],
        )

    def test_invalid_post_renders_response_with_errors(
        self, clinical_user_client, confirmed_identity_appointment
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_breast_cancer_history_item",
                kwargs={"pk": confirmed_identity_appointment.pk},
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

    def test_identity_confirmed_step_incomplete(
        self, clinical_user_client, in_progress_appointment
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_breast_cancer_history_item",
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


@pytest.mark.django_db
class TestBreastCancerHistoryUpdateView:
    def test_renders_response(self, clinical_user_client, history_item):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:update_breast_cancer_history_item",
                kwargs={
                    "pk": history_item.appointment_id,
                    "history_item_pk": history_item.pk,
                },
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_appointment(
        self, clinical_user_client, history_item
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:update_breast_cancer_history_item",
                kwargs={
                    "pk": history_item.appointment_id,
                    "history_item_pk": history_item.pk,
                },
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
                kwargs={"pk": history_item.appointment_id},
            ),
        )
        assertMessages(
            response,
            [
                messages.Message(
                    level=messages.SUCCESS,
                    message="Updated breast cancer",
                )
            ],
        )

    def test_identity_confirmed_step_incomplete(
        self, clinical_user_client, in_progress_appointment
    ):
        history_item = BreastCancerHistoryItemFactory.create(
            appointment=in_progress_appointment
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:update_breast_cancer_history_item",
                kwargs={
                    "pk": history_item.appointment_id,
                    "history_item_pk": history_item.pk,
                },
            )
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:show_appointment",
                kwargs={"pk": in_progress_appointment.pk},
            ),
        )


@pytest.mark.django_db
class TestDeleteSymptomView:
    def test_get_renders_response(self, clinical_user_client, history_item):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:delete_breast_cancer_history_item",
                kwargs={
                    "pk": history_item.appointment.pk,
                    "history_item_pk": history_item.pk,
                },
            )
        )
        assert response.status_code == 200

    def test_post_redirects_to_record_medical_information(
        self, clinical_user_client, history_item
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:delete_breast_cancer_history_item",
                kwargs={
                    "pk": history_item.appointment.pk,
                    "history_item_pk": history_item.pk,
                },
            )
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": history_item.appointment.pk},
            ),
        )
        assertMessages(
            response,
            [
                messages.Message(
                    level=messages.SUCCESS,
                    message="Deleted breast cancer",
                )
            ],
        )

    def test_the_symptom_is_deleted(self, clinical_user_client, history_item):
        clinical_user_client.http.post(
            reverse(
                "mammograms:delete_breast_cancer_history_item",
                kwargs={
                    "pk": history_item.appointment.pk,
                    "history_item_pk": history_item.pk,
                },
            )
        )

        assert not BreastCancerHistoryItem.objects.filter(pk=history_item.pk).exists()
