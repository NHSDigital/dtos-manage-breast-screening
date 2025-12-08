import pytest
from django.contrib import messages
from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertMessages, assertRedirects

from manage_breast_screening.participants.models.medical_history.implanted_medical_device_history_item import (
    ImplantedMedicalDeviceHistoryItem,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ImplantedMedicalDeviceHistoryItemFactory,
)


@pytest.mark.django_db
class TestAddImplantedMedicalDeviceHistoryView:
    def test_renders_response(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:add_implanted_medical_device_history_item",
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
                "mammograms:add_implanted_medical_device_history_item",
                kwargs={"pk": appointment.pk},
            ),
            {
                "device": ImplantedMedicalDeviceHistoryItem.Device.CARDIAC_DEVICE,
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
                    message="Implanted medical device added",
                )
            ],
        )

    def test_invalid_post_renders_response_with_errors(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_implanted_medical_device_history_item",
                kwargs={"pk": appointment.pk},
            ),
            {},
        )
        assert response.status_code == 200
        assertInHTML(
            """
                <ul class="nhsuk-list nhsuk-error-summary__list">
                    <li><a href="#id_device">Select the device type</a></li>
                </ul>
            """,
            response.text,
        )


@pytest.mark.django_db
class TestChangeImplantedMedicalDeviceHistoryView:
    @pytest.fixture
    def appointment(self, clinical_user_client):
        return AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )

    @pytest.fixture
    def history_item(self, appointment):
        return ImplantedMedicalDeviceHistoryItemFactory.create(
            appointment=appointment,
            device=ImplantedMedicalDeviceHistoryItem.Device.CARDIAC_DEVICE,
        )

    def test_renders_response(self, clinical_user_client, history_item):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:change_implanted_medical_device_history_item",
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
                "mammograms:change_implanted_medical_device_history_item",
                kwargs={"pk": appointment.pk, "history_item_pk": history_item.pk},
            ),
            {
                "device": ImplantedMedicalDeviceHistoryItem.Device.CARDIAC_DEVICE,
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
                    message="Details of implanted medical device updated",
                )
            ],
        )
