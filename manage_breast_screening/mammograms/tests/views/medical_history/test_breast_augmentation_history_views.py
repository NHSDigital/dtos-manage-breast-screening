from urllib.parse import urlencode

import pytest
from django.contrib import messages
from django.http import QueryDict
from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertMessages, assertRedirects

from manage_breast_screening.participants.models.medical_history.breast_augmentation_history_item import (
    BreastAugmentationHistoryItem,
)
from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    BreastAugmentationHistoryItemFactory,
)


@pytest.mark.django_db
class TestAddBreastAugmentationHistoryView:
    def test_renders_response(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:add_breast_augmentation_history_item",
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
                "mammograms:add_breast_augmentation_history_item",
                kwargs={"pk": appointment.pk},
            ),
            {
                "left_breast_procedures": BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS,
                "right_breast_procedures": BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS,
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
                    message="Added breast implants or augmentation",
                )
            ],
        )

    def test_invalid_post_renders_response_with_errors(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_breast_augmentation_history_item",
                kwargs={"pk": appointment.pk},
            ),
            {},
        )
        assert response.status_code == 200
        assertInHTML(
            """
                <ul class="nhsuk-list nhsuk-error-summary__list">
                    <li><a href="#id_right_breast_procedures">Select procedures for the right breast</a></li>
                    <li><a href="#id_left_breast_procedures">Select procedures for the left breast</a></li>
                </ul>
            """,
            response.text,
        )


@pytest.mark.django_db
class TestChangeBreastAugmentationHistoryView:
    @pytest.fixture
    def appointment(self, clinical_user_client):
        return AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )

    @pytest.fixture
    def history_item(self, appointment):
        return BreastAugmentationHistoryItemFactory.create(appointment=appointment)

    def test_renders_response(self, clinical_user_client, history_item):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:change_breast_augmentation_history_item",
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
                "mammograms:change_breast_augmentation_history_item",
                kwargs={
                    "pk": history_item.appointment_id,
                    "history_item_pk": history_item.pk,
                },
            ),
            QueryDict(
                urlencode(
                    {
                        "left_breast_procedures": [
                            BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
                        ],
                        "right_breast_procedures": [
                            BreastAugmentationHistoryItem.Procedure.BREAST_IMPLANTS
                        ],
                    },
                    doseq=True,
                )
            ),
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
                    message="Updated breast implants or augmentation",
                )
            ],
        )
