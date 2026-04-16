import pytest
from django.contrib import messages
from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertMessages, assertRedirects

from manage_breast_screening.participants.models.medical_history.implanted_medical_device_history_item import (
    ImplantedMedicalDeviceHistoryItem,
)
from manage_breast_screening.participants.tests.factories import (
    ImplantedMedicalDeviceHistoryItemFactory,
)


@pytest.mark.django_db
class TestAddImplantedMedicalDeviceHistoryView:
    def test_renders_response(
        self, clinical_user_client, confirmed_identity_appointment
    ):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:add_implanted_medical_device_history_item",
                kwargs={"pk": confirmed_identity_appointment.pk},
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_appointment(
        self, clinical_user_client, confirmed_identity_appointment
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_implanted_medical_device_history_item",
                kwargs={"pk": confirmed_identity_appointment.pk},
            ),
            {
                "device": ImplantedMedicalDeviceHistoryItem.Device.CARDIAC_DEVICE,
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
                    message="Added implanted medical device",
                )
            ],
        )

    def test_invalid_post_renders_response_with_errors(
        self, clinical_user_client, confirmed_identity_appointment
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_implanted_medical_device_history_item",
                kwargs={"pk": confirmed_identity_appointment.pk},
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

    def test_identity_confirmed_step_incomplete(
        self, clinical_user_client, in_progress_appointment
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_implanted_medical_device_history_item",
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
class TestChangeImplantedMedicalDeviceHistoryView:
    @pytest.fixture
    def history_item(self, confirmed_identity_appointment):
        return ImplantedMedicalDeviceHistoryItemFactory.create(
            appointment=confirmed_identity_appointment,
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
        self, clinical_user_client, confirmed_identity_appointment, history_item
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:change_implanted_medical_device_history_item",
                kwargs={
                    "pk": confirmed_identity_appointment.pk,
                    "history_item_pk": history_item.pk,
                },
            ),
            {
                "device": ImplantedMedicalDeviceHistoryItem.Device.CARDIAC_DEVICE,
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
                    message="Updated implanted medical device",
                )
            ],
        )

    def test_identity_confirmed_step_incomplete(
        self, clinical_user_client, in_progress_appointment
    ):
        history_item = ImplantedMedicalDeviceHistoryItemFactory.create(
            appointment=in_progress_appointment
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:change_implanted_medical_device_history_item",
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
class TestDeleteImplantedMedicalDeviceHistoryView:
    @pytest.fixture
    def history_item(self, confirmed_identity_appointment):
        return ImplantedMedicalDeviceHistoryItemFactory.create(
            appointment=confirmed_identity_appointment
        )

    def test_get_renders_response(self, clinical_user_client, history_item):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:delete_implanted_medical_device_history_item",
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
                "mammograms:delete_implanted_medical_device_history_item",
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
                    message="Deleted implanted medical device",
                )
            ],
        )

    def test_the_history_item_is_deleted(self, clinical_user_client, history_item):
        clinical_user_client.http.post(
            reverse(
                "mammograms:delete_implanted_medical_device_history_item",
                kwargs={
                    "pk": history_item.appointment.pk,
                    "history_item_pk": history_item.pk,
                },
            )
        )

        assert not ImplantedMedicalDeviceHistoryItem.objects.filter(
            pk=history_item.pk
        ).exists()

    def test_identity_confirmed_step_incomplete(
        self, clinical_user_client, in_progress_appointment
    ):
        history_item = ImplantedMedicalDeviceHistoryItemFactory.create(
            appointment=in_progress_appointment
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:delete_implanted_medical_device_history_item",
                kwargs={
                    "pk": in_progress_appointment.pk,
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
        assert ImplantedMedicalDeviceHistoryItem.objects.filter(
            pk=history_item.pk
        ).exists()
