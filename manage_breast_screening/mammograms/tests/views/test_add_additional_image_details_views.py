import pytest
from django.contrib import messages
from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertMessages, assertRedirects

from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
)


@pytest.mark.django_db
class TestAddAdditionalImageDetailsView:
    def test_renders_response(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:add_additional_image_details",
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
                "mammograms:add_additional_image_details",
                kwargs={"pk": appointment.pk},
            ),
            {
                "rmlo_count": "1",
                "rcc_count": "1",
                "right_eklund_count": "0",
                "lmlo_count": "1",
                "lcc_count": "1",
                "left_eklund_count": "0",
                "additional_details": "Some additional details",
            },
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:check_information",
                kwargs={"pk": appointment.pk},
            ),
        )
        assertMessages(
            response,
            [
                messages.Message(
                    level=messages.SUCCESS,
                    message="Added image details",
                )
            ],
        )

    def test_invalid_post_renders_response_with_errors(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_additional_image_details",
                kwargs={"pk": appointment.pk},
            ),
            {
                "rmlo_count": "-1",
                "rcc_count": "1.5",
                "right_eklund_count": "a",
                "lmlo_count": "21",
                "lcc_count": "100",
                "left_eklund_count": "",
                "additional_details": "Some additional details",
            },
        )
        assert response.status_code == 200
        assertInHTML(
            """
            <ul class="nhsuk-list nhsuk-error-summary__list">
                <li><a href="#id_rmlo_count">Number of RMLO images must be at least 0.</a></li>
                <li><a href="#id_rcc_count">Enter a valid number of RCC images.</a></li>
                <li><a href="#id_right_eklund_count">Enter a valid number of Right Eklund images.</a></li>
                <li><a href="#id_lmlo_count">Number of LMLO images must be at most 20.</a></li>
                <li><a href="#id_lcc_count">Number of LCC images must be at most 20.</a></li>
                <li><a href="#id_left_eklund_count">Enter the number of Left Eklund images.</a></li>
            </ul>
            """,
            response.text,
        )

    def test_zero_image_count_post_renders_response_with_errors(
        self, clinical_user_client
    ):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_additional_image_details",
                kwargs={"pk": appointment.pk},
            ),
            {
                "rmlo_count": "0",
                "rcc_count": "0",
                "right_eklund_count": "0",
                "lmlo_count": "0",
                "lcc_count": "0",
                "left_eklund_count": "0",
            },
        )
        assert response.status_code == 200
        assertInHTML(
            """
            <ul class="nhsuk-list nhsuk-error-summary__list">
                <li>Enter at least one image count</li>
            </ul>
            """,
            response.text,
        )
