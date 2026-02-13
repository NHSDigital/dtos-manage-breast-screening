import pytest
from django.contrib import messages
from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertMessages, assertRedirects

from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    OtherMedicalInformationFactory,
)


@pytest.mark.django_db
class TestAddOtherMedicalInformationView:
    def test_renders_response(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:add_other_medical_information",
                kwargs={"pk": appointment.pk},
            )
        )
        assert response.status_code == 200

    def test_redirects_if_already_exists(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        OtherMedicalInformationFactory.create(appointment=appointment)

        response = clinical_user_client.http.get(
            reverse(
                "mammograms:add_other_medical_information",
                kwargs={"pk": appointment.pk},
            )
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information", kwargs={"pk": appointment.pk}
            ),
        )

    def test_valid_post_redirects_to_appointment(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_other_medical_information",
                kwargs={"pk": appointment.pk},
            ),
            {
                "details": "some other medical information",
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
                    message="Added other medical information",
                )
            ],
        )

    def test_invalid_post_renders_response_with_errors(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_other_medical_information",
                kwargs={"pk": appointment.pk},
            ),
            {},
        )
        assert response.status_code == 200
        assertInHTML(
            """
                <ul class="nhsuk-list nhsuk-error-summary__list">
                    <li><a href="#id_details">Provide details of any relevant health conditions or medications that are not covered by symptoms or medical history questions</a></li>
                </ul>
            """,
            response.text,
        )


@pytest.mark.django_db
class TestChangeOtherMedicalInformationView:
    @pytest.fixture
    def appointment(self, clinical_user_client):
        return AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )

    @pytest.fixture
    def other_medical_information(self, appointment):
        return OtherMedicalInformationFactory.create(appointment=appointment)

    def test_renders_response(self, clinical_user_client, other_medical_information):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:change_other_medical_information",
                kwargs={
                    "pk": other_medical_information.appointment.pk,
                    "other_medical_information_pk": other_medical_information.pk,
                },
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_appointment(
        self, clinical_user_client, appointment, other_medical_information
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:change_other_medical_information",
                kwargs={
                    "pk": appointment.pk,
                    "other_medical_information_pk": other_medical_information.pk,
                },
            ),
            {
                "details": "some updated other medical information",
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
                    message="Updated other medical information",
                )
            ],
        )
