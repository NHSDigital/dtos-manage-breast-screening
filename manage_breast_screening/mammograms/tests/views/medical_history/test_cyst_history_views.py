import pytest
from django.contrib import messages
from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertMessages, assertRedirects

from manage_breast_screening.participants.models.medical_history.cyst_history_item import (
    CystHistoryItem,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    CystHistoryItemFactory,
)


@pytest.mark.django_db
class TestAddCystHistoryView:
    def test_renders_response(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:add_cyst_history_item",
                kwargs={"pk": appointment.pk},
            )
        )
        assert response.status_code == 200

    def test_redirects_if_already_exists(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        CystHistoryItemFactory.create(appointment=appointment)

        response = clinical_user_client.http.get(
            reverse(
                "mammograms:add_cyst_history_item",
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
                "mammograms:add_cyst_history_item",
                kwargs={"pk": appointment.pk},
            ),
            {
                "treatment": CystHistoryItem.Treatment.DRAINAGE_OR_REMOVAL,
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
                    message="Added cysts",
                )
            ],
        )

    def test_invalid_post_renders_response_with_errors(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_cyst_history_item",
                kwargs={"pk": appointment.pk},
            ),
            {},
        )
        assert response.status_code == 200
        assertInHTML(
            """
                <ul class="nhsuk-list nhsuk-error-summary__list">
                    <li><a href="#id_treatment">Select the treatment type</a></li>
                </ul>
            """,
            response.text,
        )


@pytest.mark.django_db
class TestChangeCystHistoryView:
    @pytest.fixture
    def appointment(self, clinical_user_client):
        return AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )

    @pytest.fixture
    def history_item(self, appointment):
        return CystHistoryItemFactory.create(
            appointment=appointment, treatment=CystHistoryItem.Treatment.NO_TREATMENT
        )

    def test_renders_response(self, clinical_user_client, history_item):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:change_cyst_history_item",
                kwargs={
                    "pk": history_item.appointment.pk,
                    "history_item_pk": history_item.pk,
                },
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_appointment(
        self, clinical_user_client, appointment, history_item
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:change_cyst_history_item",
                kwargs={"pk": appointment.pk, "history_item_pk": history_item.pk},
            ),
            {
                "treatment": CystHistoryItem.Treatment.DRAINAGE_OR_REMOVAL,
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
                    message="Updated cysts",
                )
            ],
        )
