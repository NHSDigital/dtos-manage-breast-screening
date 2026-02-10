import pytest
from django.contrib import messages
from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertMessages, assertRedirects

from manage_breast_screening.participants.models.other_information.hormone_replacement_therapy import (
    HormoneReplacementTherapy,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    HormoneReplacementTherapyFactory,
)


@pytest.mark.django_db
class TestAddHormoneReplacementTherapyView:
    def test_renders_response(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:add_hormone_replacement_therapy",
                kwargs={"pk": appointment.pk},
            )
        )
        assert response.status_code == 200

    def test_redirects_if_already_exists(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        HormoneReplacementTherapyFactory.create(appointment=appointment)

        response = clinical_user_client.http.get(
            reverse(
                "mammograms:add_hormone_replacement_therapy",
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
                "mammograms:add_hormone_replacement_therapy",
                kwargs={"pk": appointment.pk},
            ),
            {
                "status": HormoneReplacementTherapy.Status.NO,
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
                    message="Added hormone replacement therapy",
                )
            ],
        )

    def test_invalid_post_renders_response_with_errors(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_hormone_replacement_therapy",
                kwargs={"pk": appointment.pk},
            ),
            {},
        )
        assert response.status_code == 200
        assertInHTML(
            """
                <ul class="nhsuk-list nhsuk-error-summary__list">
                    <li><a href="#id_status">Select whether they are currently taking HRT or not</a></li>
                </ul>
            """,
            response.text,
        )


@pytest.mark.django_db
class TestChangeHormoneReplacementTherapyView:
    @pytest.fixture
    def appointment(self, clinical_user_client):
        return AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )

    @pytest.fixture
    def hrt(self, appointment):
        return HormoneReplacementTherapyFactory.create(appointment=appointment)

    def test_renders_response(self, clinical_user_client, hrt):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:change_hormone_replacement_therapy",
                kwargs={
                    "pk": hrt.appointment.pk,
                    "hrt_pk": hrt.pk,
                },
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_appointment(
        self, clinical_user_client, appointment, hrt
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:change_hormone_replacement_therapy",
                kwargs={"pk": appointment.pk, "hrt_pk": hrt.pk},
            ),
            {
                "status": HormoneReplacementTherapy.Status.NO,
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
                    message="Updated hormone replacement therapy",
                )
            ],
        )
