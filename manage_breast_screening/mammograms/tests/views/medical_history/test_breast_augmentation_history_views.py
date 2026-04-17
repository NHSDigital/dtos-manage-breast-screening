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
    BreastAugmentationHistoryItemFactory,
)


@pytest.mark.django_db
class TestAddBreastAugmentationHistoryView:
    def test_renders_response(
        self, clinical_user_client, confirmed_identity_appointment
    ):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:add_breast_augmentation_history_item",
                kwargs={"pk": confirmed_identity_appointment.pk},
            )
        )
        assert response.status_code == 200

    def test_valid_post_redirects_to_appointment(
        self, clinical_user_client, confirmed_identity_appointment
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_breast_augmentation_history_item",
                kwargs={"pk": confirmed_identity_appointment.pk},
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
                kwargs={"pk": confirmed_identity_appointment.pk},
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

    def test_invalid_post_renders_response_with_errors(
        self, clinical_user_client, confirmed_identity_appointment
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_breast_augmentation_history_item",
                kwargs={"pk": confirmed_identity_appointment.pk},
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

    def test_redirects_if_already_exists(
        self, clinical_user_client, confirmed_identity_appointment
    ):
        BreastAugmentationHistoryItemFactory.create(
            appointment=confirmed_identity_appointment
        )

        response = clinical_user_client.http.get(
            reverse(
                "mammograms:add_breast_augmentation_history_item",
                kwargs={"pk": confirmed_identity_appointment.pk},
            )
        )
        assertRedirects(
            response,
            reverse(
                "mammograms:record_medical_information",
                kwargs={"pk": confirmed_identity_appointment.pk},
            ),
        )

    def test_identity_confirmed_step_incomplete(
        self, clinical_user_client, in_progress_appointment
    ):
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:add_breast_augmentation_history_item",
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
class TestChangeBreastAugmentationHistoryView:
    @pytest.fixture
    def history_item(self, confirmed_identity_appointment):
        return BreastAugmentationHistoryItemFactory.create(
            appointment=confirmed_identity_appointment
        )

    def test_renders_response(self, clinical_user_client, history_item):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:update_breast_augmentation_history_item",
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
                "mammograms:update_breast_augmentation_history_item",
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

    def test_identity_confirmed_step_incomplete(
        self, clinical_user_client, in_progress_appointment
    ):
        history_item = BreastAugmentationHistoryItemFactory.create(
            appointment=in_progress_appointment
        )
        response = clinical_user_client.http.post(
            reverse(
                "mammograms:update_breast_augmentation_history_item",
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
class TestDeleteBreastAugmentationHistoryView:
    @pytest.fixture
    def history_item(self, confirmed_identity_appointment):
        return BreastAugmentationHistoryItemFactory.create(
            appointment=confirmed_identity_appointment
        )

    def test_get_renders_response(self, clinical_user_client, history_item):
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:delete_breast_augmentation_history_item",
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
                "mammograms:delete_breast_augmentation_history_item",
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
                    message="Deleted breast implants or augmentation",
                )
            ],
        )

    def test_the_history_item_is_deleted(self, clinical_user_client, history_item):
        clinical_user_client.http.post(
            reverse(
                "mammograms:delete_breast_augmentation_history_item",
                kwargs={
                    "pk": history_item.appointment.pk,
                    "history_item_pk": history_item.pk,
                },
            )
        )

        assert not BreastAugmentationHistoryItem.objects.filter(
            pk=history_item.pk
        ).exists()
